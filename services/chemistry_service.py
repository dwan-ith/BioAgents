"""RDKit-backed molecular structure analysis and rule-based transformations."""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Any, Iterable

from rdkit import Chem, DataStructs
from rdkit.Chem import BRICS, Crippen, Descriptors, Draw, Lipinski, QED, rdMolDescriptors
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams
from rdkit.Chem import rdChemReactions
from rdkit.Chem.rdFingerprintGenerator import GetMorganGenerator

from exceptions import InvalidInputError
from services.base_service import BioAgentService, ServiceIdentity


class ChemistryService(BioAgentService):
    """Computes reproducible structure-derived properties without an LLM."""

    identity = ServiceIdentity("ChemistryAgent", "RDKit structure analysis", "/api/workflows/discovery")

    _MAX_SMILES_LENGTH = 2_000
    _MAX_REACTION_LENGTH = 4_000
    _fingerprints = GetMorganGenerator(radius=2, fpSize=2048)

    def __init__(self) -> None:
        params = FilterCatalogParams()
        params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS)
        params.AddCatalog(FilterCatalogParams.FilterCatalogs.BRENK)
        self._alert_catalog = FilterCatalog(params)

    def analyze(self, smiles: str, *, name: str | None = None, include_svg: bool = True) -> dict[str, Any]:
        molecule = self.parse_smiles(smiles)
        canonical = Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)
        descriptors = self._descriptors(molecule)
        alerts = self._alerts(molecule)
        gates = self._quality_gates(descriptors, alerts)

        result: dict[str, Any] = {
            "name": (name or "").strip() or None,
            "input_smiles": smiles.strip(),
            "canonical_smiles": canonical,
            "inchi": Chem.MolToInchi(molecule),
            "inchikey": Chem.MolToInchiKey(molecule),
            "formula": rdMolDescriptors.CalcMolFormula(molecule),
            "descriptors": descriptors,
            "alerts": alerts,
            "quality_gates": gates,
            "method": {
                "engine": "RDKit",
                "scope": "2D structure standardization, descriptors, fingerprints, and catalog alerts",
                "not_supported": [
                    "binding affinity prediction",
                    "clinical safety prediction",
                    "toxicity prediction",
                    "synthetic feasibility prediction",
                ],
            },
        }
        if include_svg:
            result["structure_svg"] = self.depict(molecule, legend=name or canonical)
        return result

    def compare(self, left_smiles: str, right_smiles: str) -> dict[str, Any]:
        left = self.parse_smiles(left_smiles)
        right = self.parse_smiles(right_smiles)
        left_fp = self._fingerprints.GetFingerprint(left)
        right_fp = self._fingerprints.GetFingerprint(right)
        similarity = float(DataStructs.TanimotoSimilarity(left_fp, right_fp))
        left_descriptors = self._descriptors(left)
        right_descriptors = self._descriptors(right)
        numeric_fields = (
            "molecular_weight",
            "clogp",
            "tpsa",
            "h_bond_donors",
            "h_bond_acceptors",
            "rotatable_bonds",
            "qed",
        )
        return {
            "tanimoto_similarity": round(similarity, 4),
            "fingerprint": "Morgan radius 2, 2048 bits",
            "descriptor_delta": {
                field: round(float(right_descriptors[field]) - float(left_descriptors[field]), 4)
                for field in numeric_fields
            },
            "interpretation": self._similarity_interpretation(similarity),
            "limitation": "2D fingerprint similarity is not evidence of shared efficacy or safety.",
        }

    def enumerate_analogs(self, seed_smiles: str, *, limit: int = 8) -> list[dict[str, Any]]:
        """Deterministically recombine the seed's own BRICS fragments.

        This produces valid graph hypotheses, not target-activity predictions. Molecules
        with no useful BRICS decomposition correctly return an empty list.
        """
        if not 1 <= limit <= 20:
            raise InvalidInputError("Analog limit must be between 1 and 20.")
        seed = self.parse_smiles(seed_smiles)
        seed_canonical = Chem.MolToSmiles(seed, canonical=True, isomericSmiles=True)
        fragments = sorted(BRICS.BRICSDecompose(seed))
        if len(fragments) < 2:
            return []

        fragment_molecules = [Chem.MolFromSmiles(fragment) for fragment in fragments]
        fragment_molecules = [molecule for molecule in fragment_molecules if molecule is not None]
        seed_fp = self._fingerprints.GetFingerprint(seed)
        accepted: list[dict[str, Any]] = []
        seen = {seed_canonical}

        products: Iterable[Chem.Mol] = BRICS.BRICSBuild(
            fragment_molecules,
            onlyCompleteMols=True,
            uniquify=True,
            scrambleReagents=False,
        )
        for index, product in enumerate(products):
            if index >= 500 or len(accepted) >= limit:
                break
            try:
                Chem.SanitizeMol(product)
            except (ValueError, RuntimeError):
                continue
            canonical = Chem.MolToSmiles(product, canonical=True, isomericSmiles=True)
            if canonical in seen or "." in canonical:
                continue
            seen.add(canonical)
            descriptors = self._descriptors(product)
            if not 80.0 <= descriptors["molecular_weight"] <= 650.0:
                continue
            similarity = float(
                DataStructs.TanimotoSimilarity(seed_fp, self._fingerprints.GetFingerprint(product))
            )
            if not 0.20 <= similarity <= 0.95:
                continue
            alerts = self._alerts(product)
            gates = self._quality_gates(descriptors, alerts)
            accepted.append({
                "name": f"BRICS analog {len(accepted) + 1}",
                "canonical_smiles": canonical,
                "formula": rdMolDescriptors.CalcMolFormula(product),
                "descriptors": descriptors,
                "alerts": alerts,
                "quality_gates": gates,
                "similarity_to_seed": round(similarity, 4),
                "generation_source": "rdkit-brics-local",
                "generation_note": "Recombined only from retrosynthetically permitted fragments in the seed structure.",
                "structure_svg": self.depict(product, legend=f"BRICS analog {len(accepted) + 1}"),
            })
        return accepted

    def run_reaction(self, reactants: list[str], reaction_smarts: str, *, limit: int = 24) -> dict[str, Any]:
        if not isinstance(reactants, list) or not 1 <= len(reactants) <= 4:
            raise InvalidInputError("Reactants must be an array containing one to four SMILES strings.")
        cleaned_smarts = reaction_smarts.strip() if isinstance(reaction_smarts, str) else ""
        if not cleaned_smarts or len(cleaned_smarts) > self._MAX_REACTION_LENGTH:
            raise InvalidInputError("Reaction SMARTS must be a non-empty string of at most 4000 characters.")
        molecules = tuple(self.parse_smiles(smiles) for smiles in reactants)
        try:
            reaction = rdChemReactions.ReactionFromSmarts(cleaned_smarts)
            if reaction is None:
                raise ValueError("RDKit returned no reaction")
            reaction.Initialize()
        except (ValueError, RuntimeError) as exc:
            raise InvalidInputError("Reaction SMARTS is not a valid RDKit reaction transform.") from exc
        expected = reaction.GetNumReactantTemplates()
        if expected != len(molecules):
            raise InvalidInputError(
                f"Reaction transform expects {expected} reactant(s), but {len(molecules)} were supplied."
            )

        try:
            product_sets = reaction.RunReactants(molecules, maxProducts=limit * 4)
        except (ValueError, RuntimeError) as exc:
            raise InvalidInputError("The supplied reactants are incompatible with this reaction transform.") from exc

        products: list[dict[str, Any]] = []
        seen: set[str] = set()
        for product_set in product_sets:
            sanitized: list[Chem.Mol] = []
            failed = False
            for product in product_set:
                try:
                    Chem.SanitizeMol(product)
                except (ValueError, RuntimeError):
                    failed = True
                    break
                sanitized.append(product)
            if failed:
                continue
            smiles = ".".join(sorted(Chem.MolToSmiles(product, isomericSmiles=True) for product in sanitized))
            if smiles in seen:
                continue
            seen.add(smiles)
            products.append({
                "product_smiles": smiles,
                "product_count": len(sanitized),
                "structure_svg": self.depict(sanitized[0], legend=smiles) if len(sanitized) == 1 else None,
            })
            if len(products) >= limit:
                break

        return {
            "status": "PRODUCTS_ENUMERATED" if products else "NO_MATCHING_PRODUCTS",
            "reactants": [Chem.MolToSmiles(molecule, isomericSmiles=True) for molecule in molecules],
            "reaction_smarts": cleaned_smarts,
            "products": products,
            "product_set_count": len(products),
            "method": "RDKit reaction SMARTS application",
            "limitation": (
                "This applies an explicit user-supplied transform. It does not predict reaction conditions, "
                "yield, selectivity, kinetics, or whether the reaction is experimentally feasible."
            ),
        }

    def parse_smiles(self, smiles: str) -> Chem.Mol:
        cleaned = smiles.strip() if isinstance(smiles, str) else ""
        if not cleaned:
            raise InvalidInputError("SMILES must be a non-empty string.")
        if len(cleaned) > self._MAX_SMILES_LENGTH:
            raise InvalidInputError("SMILES must be 2000 characters or fewer.")
        molecule = Chem.MolFromSmiles(cleaned)
        if molecule is None or molecule.GetNumHeavyAtoms() == 0:
            raise InvalidInputError("RDKit could not parse the supplied SMILES into a valid molecule.")
        return molecule

    @staticmethod
    @lru_cache(maxsize=512)
    def _cached_svg(canonical_smiles: str, legend: str) -> str:
        molecule = Chem.MolFromSmiles(canonical_smiles)
        return str(
            Draw.MolsToGridImage(
                [molecule],
                molsPerRow=1,
                subImgSize=(420, 280),
                legends=[legend[:80]],
                useSVG=True,
            )
        )

    def depict(self, molecule: Chem.Mol, *, legend: str) -> str:
        canonical = Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)
        return self._cached_svg(canonical, legend)

    @staticmethod
    def _descriptors(molecule: Chem.Mol) -> dict[str, Any]:
        values = {
            "molecular_weight": Descriptors.MolWt(molecule),
            "exact_mass": Descriptors.ExactMolWt(molecule),
            "clogp": Crippen.MolLogP(molecule),
            "tpsa": rdMolDescriptors.CalcTPSA(molecule),
            "h_bond_donors": Lipinski.NumHDonors(molecule),
            "h_bond_acceptors": Lipinski.NumHAcceptors(molecule),
            "rotatable_bonds": Lipinski.NumRotatableBonds(molecule),
            "ring_count": rdMolDescriptors.CalcNumRings(molecule),
            "aromatic_ring_count": rdMolDescriptors.CalcNumAromaticRings(molecule),
            "heavy_atom_count": molecule.GetNumHeavyAtoms(),
            "formal_charge": sum(atom.GetFormalCharge() for atom in molecule.GetAtoms()),
            "fraction_csp3": rdMolDescriptors.CalcFractionCSP3(molecule),
            "qed": QED.qed(molecule),
            "fragment_count": len(Chem.GetMolFrags(molecule)),
        }
        return {
            key: round(float(value), 4) if isinstance(value, float) and math.isfinite(value) else value
            for key, value in values.items()
        }

    def _alerts(self, molecule: Chem.Mol) -> list[dict[str, str]]:
        matches = self._alert_catalog.GetMatches(molecule)
        return [
            {"catalog": "PAINS/BRENK", "description": match.GetDescription()}
            for match in matches[:20]
        ]

    @staticmethod
    def _quality_gates(descriptors: dict[str, Any], alerts: list[dict[str, str]]) -> dict[str, Any]:
        rules = {
            "molecular_weight_le_500": descriptors["molecular_weight"] <= 500,
            "clogp_le_5": descriptors["clogp"] <= 5,
            "h_bond_donors_le_5": descriptors["h_bond_donors"] <= 5,
            "h_bond_acceptors_le_10": descriptors["h_bond_acceptors"] <= 10,
            "rotatable_bonds_le_10": descriptors["rotatable_bonds"] <= 10,
            "tpsa_le_140": descriptors["tpsa"] <= 140,
            "single_fragment": descriptors["fragment_count"] == 1,
            "no_catalog_alerts": not alerts,
        }
        ro5_fields = (
            "molecular_weight_le_500",
            "clogp_le_5",
            "h_bond_donors_le_5",
            "h_bond_acceptors_le_10",
        )
        ro5_violations = sum(not rules[field] for field in ro5_fields)
        warnings = []
        if ro5_violations:
            warnings.append(f"{ro5_violations} Rule-of-Five threshold(s) exceeded.")
        if not rules["single_fragment"]:
            warnings.append("Structure contains multiple disconnected fragments or counterions.")
        if alerts:
            warnings.append(f"{len(alerts)} PAINS/BRENK catalog alert(s) matched; review manually.")
        if descriptors["qed"] < 0.35:
            warnings.append("Low QED suggests weak general drug-like property balance.")
        status = "PASS" if not warnings else "REVIEW"
        if ro5_violations >= 2 or not rules["single_fragment"]:
            status = "FAIL"
        return {
            "status": status,
            "rules": rules,
            "rule_of_five_violations": ro5_violations,
            "veber_like_pass": rules["rotatable_bonds_le_10"] and rules["tpsa_le_140"],
            "warnings": warnings,
            "disclaimer": "Heuristic developability gates are not efficacy, toxicity, or clinical-safety predictions.",
        }

    @staticmethod
    def _similarity_interpretation(similarity: float) -> str:
        if similarity >= 0.85:
            return "Very close 2D analog"
        if similarity >= 0.65:
            return "Related 2D chemical space"
        if similarity >= 0.40:
            return "Moderate structural relationship"
        return "Low 2D structural similarity"
