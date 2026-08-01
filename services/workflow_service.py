"""Auditable, evidence-aware drug-discovery workflows."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from exceptions import BioAgentError, ExternalAPIError, InvalidInputError
from services.base_service import BioAgentService, ServiceIdentity
from services.chembl_service import ChEMBLService
from services.chemistry_service import ChemistryService
from services.database_service import DatabaseService
from services.llm_service import LLMService


class DiscoveryWorkflowService(BioAgentService):
    identity = ServiceIdentity("OrchestratorAgent", "auditable discovery workflows", "/api/workflows/discovery")

    def __init__(
        self,
        *,
        chemistry: ChemistryService,
        database: DatabaseService,
        evidence: ChEMBLService,
        llm: LLMService,
    ) -> None:
        self.chemistry = chemistry
        self.database = database
        self.evidence = evidence
        self.llm = llm

    def discover(
        self,
        *,
        seed: str,
        input_type: str,
        objective: str,
        target: str | None,
        max_candidates: int,
    ) -> dict[str, Any]:
        self._validate_request(seed, input_type, objective, target, max_candidates)
        trace: list[dict[str, Any]] = []
        started = time.monotonic()
        profile, identity = self._step(
            trace,
            "StructureAgent",
            "resolve and standardize seed structure",
            lambda: self.resolve_structure(seed, input_type=input_type),
        )
        evidence = self._step(
            trace,
            "EvidenceAgent",
            "retrieve ChEMBL molecule and assay evidence",
            lambda: self._safe_evidence(profile["inchikey"]),
        )
        candidates, rejected = self._step(
            trace,
            "CandidateAgent",
            "generate, validate, deduplicate, and score analog hypotheses",
            lambda: self._candidate_pipeline(
                profile,
                objective=objective,
                target=target,
                max_candidates=max_candidates,
            ),
        )
        elapsed_ms = round((time.monotonic() - started) * 1000, 1)
        status = "CANDIDATES_PROPOSED" if candidates else "INSUFFICIENT_CANDIDATES"
        return {
            "schema_version": "bioagents.discovery.v2",
            "run_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "objective": objective.strip(),
            "target": target.strip() if target else None,
            "seed": profile,
            "identity": identity,
            "evidence": evidence,
            "candidates": candidates,
            "rejected_candidate_count": len(rejected),
            "rejected_candidates": rejected[:10],
            "workflow": {
                "execution_mode": "cooperative in-process agents",
                "distributed_runtime": "optional uAgents adapters; not used by this HTTP request",
                "elapsed_ms": elapsed_ms,
                "trace": trace,
            },
            "decision_boundary": {
                "supported": [
                    "structure validation and standardization",
                    "2D descriptors, fingerprints, and catalog alerts",
                    "live PubChem identity and ChEMBL assay retrieval",
                    "transparent analog triage and provenance",
                ],
                "not_claimed": [
                    "target binding prediction",
                    "reaction yield or synthetic feasibility",
                    "toxicity or clinical safety",
                    "global chemical novelty",
                    "experimental validation",
                ],
            },
        }

    def compare(self, *, left: str, right: str, input_type: str) -> dict[str, Any]:
        if not left.strip() or not right.strip():
            raise InvalidInputError("Both compounds are required for comparison.")
        trace: list[dict[str, Any]] = []
        left_profile, left_identity = self._step(
            trace, "StructureAgent-A", "resolve first compound", lambda: self.resolve_structure(left, input_type=input_type)
        )
        right_profile, right_identity = self._step(
            trace, "StructureAgent-B", "resolve second compound", lambda: self.resolve_structure(right, input_type=input_type)
        )
        structure = self._step(
            trace,
            "AnalysisAgent",
            "compute deterministic 2D structural comparison",
            lambda: self.chemistry.compare(left_profile["canonical_smiles"], right_profile["canonical_smiles"]),
        )
        left_evidence = self._step(
            trace, "EvidenceAgent-A", "retrieve first compound evidence", lambda: self._safe_evidence(left_profile["inchikey"])
        )
        right_evidence = self._step(
            trace, "EvidenceAgent-B", "retrieve second compound evidence", lambda: self._safe_evidence(right_profile["inchikey"])
        )
        left_targets = {
            item["target_chembl_id"]: item
            for item in left_evidence.get("targets", [])
            if self._is_supported_overlap_target(item)
        }
        right_targets = {
            item["target_chembl_id"]: item
            for item in right_evidence.get("targets", [])
            if self._is_supported_overlap_target(item)
        }
        shared_ids = sorted(set(left_targets).intersection(right_targets))
        shared_targets = [
            {
                "target_chembl_id": target_id,
                "target_name": left_targets[target_id]["target_name"],
                "left_max_pchembl": left_targets[target_id]["max_pchembl_value"],
                "right_max_pchembl": right_targets[target_id]["max_pchembl_value"],
            }
            for target_id in shared_ids
        ]
        assessment = "POTENTIAL_TARGET_OVERLAP" if shared_targets else "INSUFFICIENT_EVIDENCE"
        return {
            "schema_version": "bioagents.comparison.v2",
            "run_id": str(uuid.uuid4()),
            "assessment": assessment,
            "left": {"structure": left_profile, "identity": left_identity, "evidence": left_evidence},
            "right": {"structure": right_profile, "identity": right_identity, "evidence": right_evidence},
            "structure_comparison": structure,
            "shared_targets": shared_targets,
            "interpretation": (
                "Shared ChEMBL assay targets warrant mechanistic review; they do not establish a drug-drug interaction."
                if shared_targets
                else "No supported shared target was found in the bounded evidence retrieved. This is not evidence of no interaction."
            ),
            "clinical_interaction_prediction": "NOT_PERFORMED",
            "workflow": {"execution_mode": "cooperative in-process agents", "trace": trace},
        }

    @staticmethod
    def _is_supported_overlap_target(target: dict[str, Any]) -> bool:
        name = str(target.get("target_name") or "").strip().casefold()
        target_id = str(target.get("target_chembl_id") or "").strip()
        unsupported_names = {
            "",
            "unchecked",
            "non-protein target",
            "unknown",
            "unclassified",
        }
        return bool(target_id) and name not in unsupported_names

    def reaction(self, *, reactants: list[str], reaction_smarts: str) -> dict[str, Any]:
        trace: list[dict[str, Any]] = []
        result = self._step(
            trace,
            "ReactionAgent",
            "validate structures and apply explicit reaction SMARTS",
            lambda: self.chemistry.run_reaction(reactants, reaction_smarts),
        )
        return {
            "schema_version": "bioagents.reaction.v2",
            "run_id": str(uuid.uuid4()),
            **result,
            "workflow": {"execution_mode": "deterministic local RDKit", "trace": trace},
        }

    def resolve_structure(self, query: str, *, input_type: str) -> tuple[dict[str, Any], dict[str, Any]]:
        cleaned = query.strip() if isinstance(query, str) else ""
        if not cleaned or len(cleaned) > 2_000:
            raise InvalidInputError("Compound input must be a non-empty string of at most 2000 characters.")
        normalized_type = input_type.strip().lower() if isinstance(input_type, str) else ""
        if normalized_type not in {"name", "smiles", "auto"}:
            raise InvalidInputError("input_type must be 'name', 'smiles', or 'auto'.")

        if normalized_type in {"smiles", "auto"}:
            try:
                structure = self.chemistry.analyze(cleaned, include_svg=True)
                return structure, {
                    "resolution_source": "user-supplied SMILES",
                    "query": cleaned,
                    "pubchem": None,
                    "provenance": [],
                }
            except InvalidInputError:
                if normalized_type == "smiles":
                    raise

        pubchem = self.database.fetch_pubchem(cleaned).to_dict()
        smiles = pubchem.get("isomeric_smiles") or pubchem.get("connectivity_smiles")
        if not smiles:
            raise ExternalAPIError("PubChem resolved the name but did not return a usable structure.")
        name = pubchem.get("iupac_name") or cleaned
        structure = self.chemistry.analyze(smiles, name=name, include_svg=True)
        return structure, {
            "resolution_source": "PubChem PUG REST",
            "query": cleaned,
            "pubchem": pubchem,
            "provenance": [{
                "provider": "PubChem",
                "resource": "compound identity and computed properties",
                "url": pubchem["source_url"],
                "retrieved_live": True,
            }],
        }

    def _candidate_pipeline(
        self,
        seed_profile: dict[str, Any],
        *,
        objective: str,
        target: str | None,
        max_candidates: int,
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        candidates: list[dict[str, Any]] = []
        rejected: list[dict[str, str]] = []
        seen = {seed_profile["canonical_smiles"]}

        proposals = self.llm.propose_drug_candidates(
            seed_profile,
            objective=objective,
            target=target,
            limit=max_candidates,
        )
        for proposal in proposals:
            try:
                profile = self.chemistry.analyze(
                    proposal["smiles"],
                    name=proposal["name"],
                    include_svg=True,
                )
            except BioAgentError as exc:
                rejected.append({"name": proposal.get("name", "Unnamed"), "reason": exc.message})
                continue
            canonical = profile["canonical_smiles"]
            if canonical in seen:
                rejected.append({"name": proposal["name"], "reason": "Duplicate of seed or prior candidate."})
                continue
            seen.add(canonical)
            comparison = self.chemistry.compare(seed_profile["canonical_smiles"], canonical)
            candidate = {
                **profile,
                "generation_source": "openai-primary-rdkit-validated",
                "intended_change": proposal["intended_change"],
                "rationale": proposal["rationale"],
                "hypothesis": proposal["hypothesis"],
                "similarity_to_seed": comparison["tanimoto_similarity"],
                "validation": "VALID_RDKIT_STRUCTURE",
            }
            candidate["triage"] = self._score_candidate(candidate)
            candidates.append(candidate)
            if len(candidates) >= max_candidates:
                break

        if len(candidates) < max_candidates:
            local = self.chemistry.enumerate_analogs(
                seed_profile["canonical_smiles"],
                limit=max_candidates,
            )
            for candidate in local:
                canonical = candidate["canonical_smiles"]
                if canonical in seen:
                    continue
                seen.add(canonical)
                candidate.update({
                    "intended_change": "BRICS fragment recombination within the seed's own fragment vocabulary.",
                    "rationale": "Provides a deterministic structural hypothesis when OpenAI is unavailable or incomplete.",
                    "hypothesis": "Property balance may change; target activity is unknown and requires assay testing.",
                    "validation": "VALID_RDKIT_STRUCTURE",
                })
                candidate["triage"] = self._score_candidate(candidate)
                candidates.append(candidate)
                if len(candidates) >= max_candidates:
                    break

        candidates.sort(key=lambda item: item["triage"]["score"], reverse=True)
        for rank, candidate in enumerate(candidates, start=1):
            candidate["rank"] = rank
        return candidates, rejected

    @staticmethod
    def _score_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
        descriptors = candidate["descriptors"]
        gates = candidate["quality_gates"]
        qed_score = float(descriptors["qed"])
        property_penalty = min(
            1.0,
            gates["rule_of_five_violations"] * 0.25
            + (0.25 if not gates["veber_like_pass"] else 0.0)
            + (0.25 if not gates["rules"]["single_fragment"] else 0.0)
            + min(len(candidate["alerts"]), 3) * 0.1,
        )
        property_score = 1.0 - property_penalty
        similarity = float(candidate["similarity_to_seed"])
        similarity_window_score = max(0.0, 1.0 - abs(similarity - 0.55) / 0.55)
        score = 0.45 * qed_score + 0.35 * property_score + 0.20 * similarity_window_score
        return {
            "score": round(score, 4),
            "label": "transparent property triage; not predicted activity",
            "components": {
                "qed": round(qed_score, 4),
                "property_gate_score": round(property_score, 4),
                "similarity_window_score": round(similarity_window_score, 4),
            },
            "weights": {"qed": 0.45, "property_gate_score": 0.35, "similarity_window_score": 0.20},
            "target_activity_component": None,
        }

    def _safe_evidence(self, inchikey: str) -> dict[str, Any]:
        try:
            return self.evidence.evidence_for_inchikey(inchikey)
        except ExternalAPIError as exc:
            return self.evidence.unavailable_evidence(inchikey, exc.message)

    @staticmethod
    def _step(
        trace: list[dict[str, Any]],
        agent: str,
        operation: str,
        function: Callable[[], Any],
    ) -> Any:
        started = time.monotonic()
        try:
            result = function()
        except Exception as exc:
            trace.append({
                "agent": agent,
                "operation": operation,
                "status": "failed",
                "duration_ms": round((time.monotonic() - started) * 1000, 1),
                "error_type": type(exc).__name__,
            })
            raise
        trace.append({
            "agent": agent,
            "operation": operation,
            "status": "completed",
            "duration_ms": round((time.monotonic() - started) * 1000, 1),
        })
        return result

    @staticmethod
    def _validate_request(
        seed: str,
        input_type: str,
        objective: str,
        target: str | None,
        max_candidates: int,
    ) -> None:
        if not isinstance(seed, str) or not seed.strip():
            raise InvalidInputError("Seed compound is required.")
        if input_type not in {"name", "smiles", "auto"}:
            raise InvalidInputError("input_type must be 'name', 'smiles', or 'auto'.")
        if not isinstance(objective, str) or not 5 <= len(objective.strip()) <= 500:
            raise InvalidInputError("Objective must contain between 5 and 500 characters.")
        if target is not None and (not isinstance(target, str) or len(target.strip()) > 200):
            raise InvalidInputError("Target must be a string of at most 200 characters.")
        if isinstance(max_candidates, bool) or not isinstance(max_candidates, int) or not 1 <= max_candidates <= 12:
            raise InvalidInputError("max_candidates must be an integer between 1 and 12.")
