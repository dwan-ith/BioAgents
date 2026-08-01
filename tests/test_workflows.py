from __future__ import annotations

import unittest
from unittest.mock import patch

from exceptions import InvalidInputError
from server import app
from services.chembl_service import ChEMBLService
from services.chemistry_service import ChemistryService


ASPIRIN = "CC(=O)Oc1ccccc1C(=O)O"
ACETAMINOPHEN = "CC(=O)NC1=CC=C(O)C=C1"


class ChemistryServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chemistry = ChemistryService()

    def test_structure_analysis_is_reproducible_and_typed(self):
        first = self.chemistry.analyze(ASPIRIN, include_svg=False)
        second = self.chemistry.analyze(ASPIRIN, include_svg=False)
        self.assertEqual(first, second)
        self.assertEqual(first["formula"], "C9H8O4")
        self.assertEqual(first["canonical_smiles"], ASPIRIN)
        self.assertAlmostEqual(first["descriptors"]["molecular_weight"], 180.159, places=2)
        self.assertIn(first["quality_gates"]["status"], {"PASS", "REVIEW", "FAIL"})

    def test_invalid_smiles_is_rejected(self):
        with self.assertRaises(InvalidInputError):
            self.chemistry.analyze("C1=broken", include_svg=False)

    def test_brics_candidates_are_valid_unique_non_seed_structures(self):
        candidates = self.chemistry.enumerate_analogs(ASPIRIN, limit=5)
        self.assertGreaterEqual(len(candidates), 2)
        smiles = [candidate["canonical_smiles"] for candidate in candidates]
        self.assertEqual(len(smiles), len(set(smiles)))
        self.assertNotIn(ASPIRIN, smiles)
        self.assertTrue(all(candidate["generation_source"] == "rdkit-brics-local" for candidate in candidates))

    def test_reaction_requires_matching_reactant_arity(self):
        with self.assertRaises(InvalidInputError):
            self.chemistry.run_reaction(
                ["CC(=O)O"],
                "[C:1](=[O:2])[OH:3].[OH:4][C:5]>>[C:1](=[O:2])[O:4][C:5]",
            )

    def test_explicit_reaction_rule_enumerates_sanitized_products(self):
        result = self.chemistry.run_reaction(
            ["CC(=O)O", "CO"],
            "[C:1](=[O:2])[OH:3].[OH:4][C:5]>>[C:1](=[O:2])[O:4][C:5]",
        )
        self.assertEqual(result["status"], "PRODUCTS_ENUMERATED")
        self.assertIn("COC(C)=O", {item["product_smiles"] for item in result["products"]})
        self.assertIn("does not predict", result["limitation"])

    def test_similarity_does_not_claim_shared_efficacy(self):
        result = self.chemistry.compare(ASPIRIN, ACETAMINOPHEN)
        self.assertGreaterEqual(result["tanimoto_similarity"], 0)
        self.assertLessEqual(result["tanimoto_similarity"], 1)
        self.assertIn("not evidence", result["limitation"])


class ChEMBLNormalizationTests(unittest.TestCase):
    def test_invalid_activity_rows_are_removed_and_targets_are_grouped(self):
        rows = [
            {
                "molecule_chembl_id": "CHEMBL25",
                "target_chembl_id": "CHEMBL230",
                "target_pref_name": "COX-2",
                "target_organism": "Homo sapiens",
                "pchembl_value": "7.1",
                "standard_type": "IC50",
                "standard_value": "79",
                "standard_units": "nM",
                "standard_relation": "=",
                "assay_chembl_id": "CHEMBL_A",
                "document_chembl_id": "CHEMBL_D",
                "data_validity_comment": None,
            },
            {
                "target_chembl_id": "CHEMBL230",
                "pchembl_value": "8.0",
                "data_validity_comment": "Outside typical range",
            },
        ]
        activities = ChEMBLService._normalize_activities(rows)
        targets = ChEMBLService._summarize_targets(activities)
        self.assertEqual(len(activities), 1)
        self.assertEqual(targets[0]["measurement_count"], 1)
        self.assertEqual(targets[0]["max_pchembl_value"], 7.1)


class WorkflowApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_discovery_workflow_returns_validated_candidates_and_trace(self):
        unavailable = {
            "status": "EVIDENCE_UNAVAILABLE",
            "inchikey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
            "targets": [],
            "activities": [],
            "evidence_grade": "NONE",
            "reason": "offline test",
            "provenance": [],
        }
        with patch("server._chembl.evidence_for_inchikey", return_value=unavailable):
            response = self.client.post("/api/workflows/discovery", json={
                "seed": ASPIRIN,
                "input_type": "smiles",
                "objective": "Improve property balance while retaining an aspirin-like scaffold.",
                "target": "PTGS2",
                "max_candidates": 3,
            })
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["schema_version"], "bioagents.discovery.v2")
        self.assertEqual(len(payload["candidates"]), 3)
        self.assertTrue(all(item["validation"] == "VALID_RDKIT_STRUCTURE" for item in payload["candidates"]))
        self.assertTrue(all(item["triage"]["target_activity_component"] is None for item in payload["candidates"]))
        self.assertEqual([item["rank"] for item in payload["candidates"]], [1, 2, 3])
        self.assertEqual(len(payload["workflow"]["trace"]), 3)

    def test_comparison_without_target_evidence_is_insufficient_not_safe(self):
        unavailable = {
            "status": "NO_CHEMBL_MATCH",
            "targets": [],
            "activities": [],
            "evidence_grade": "NONE",
            "provenance": [],
        }
        with patch("server._chembl.evidence_for_inchikey", return_value=unavailable):
            response = self.client.post("/api/workflows/compare", json={
                "left": ASPIRIN,
                "right": ACETAMINOPHEN,
                "input_type": "smiles",
            })
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["assessment"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(payload["clinical_interaction_prediction"], "NOT_PERFORMED")
        self.assertIn("not evidence of no interaction", payload["interpretation"])

    def test_comparison_excludes_placeholder_chembl_targets(self):
        placeholder_evidence = {
            "status": "EVIDENCE_FOUND",
            "targets": [{
                "target_chembl_id": "CHEMBL612545",
                "target_name": "Unchecked",
                "max_pchembl_value": 6.79,
                "measurement_count": 1,
            }],
            "activities": [],
            "evidence_grade": "LIMITED",
            "provenance": [],
        }
        with patch(
            "server._chembl.evidence_for_inchikey",
            side_effect=[placeholder_evidence, placeholder_evidence],
        ):
            response = self.client.post("/api/workflows/compare", json={
                "left": ASPIRIN,
                "right": ACETAMINOPHEN,
                "input_type": "smiles",
            })
        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["assessment"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(payload["shared_targets"], [])

    def test_capabilities_publish_unsupported_claims(self):
        response = self.client.get("/api/capabilities")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("toxicity prediction", payload["unsupported_claims"])
        self.assertTrue(any(item["id"] == "structure" for item in payload["capabilities"]))


if __name__ == "__main__":
    unittest.main()
