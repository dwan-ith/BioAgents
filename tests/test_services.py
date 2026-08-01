from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from exceptions import InvalidInputError, KnowledgeBaseError
from knowledge.metta_handler import MeTTaKnowledgeBase
from models.molecule import CandidateCompound, DiscoveryResult, MoleculeProperties
from services.analysis_service import AnalysisService
from services.database_service import DatabaseService
from services.feedback_service import FeedbackService
from services.llm_service import LLMService


class FakeResponse:
    def __init__(self, status_code: int, payload=None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text or (json.dumps(payload) if payload is not None else "")

    def json(self):
        if self._payload is None:
            raise ValueError("not JSON")
        return self._payload


def chat_response(content: str) -> FakeResponse:
    return FakeResponse(200, {"choices": [{"message": {"content": content}}]})


class LLMServiceTests(unittest.TestCase):
    @patch("services.llm_service.requests.post")
    def test_compound_analysis_uses_stable_json_contract(self, post):
        post.return_value = chat_response(json.dumps({
            "summary": "Useful profile.",
            "strengths": ["stable"],
            "risks": ["unvalidated"],
            "next_experiments": ["bench test"],
        }))
        service = LLMService(api_key="test-key", model="gpt-4o-mini")

        result = service.compound_analysis({"molecule": "HZSM_5"})

        self.assertEqual(result["summary"], "Useful profile.")
        request_body = post.call_args.kwargs["json"]
        self.assertEqual(request_body["response_format"], {"type": "json_object"})
        self.assertNotIn("test-key", json.dumps(request_body))

    @patch("services.llm_service.requests.post")
    def test_text_request_does_not_send_null_response_format(self, post):
        post.return_value = chat_response("A concise insight.")
        service = LLMService(api_key="test-key")

        result = service.generate_insight("compound profile", {"molecule": "HZSM_5"})

        self.assertEqual(result, "A concise insight.")
        self.assertNotIn("response_format", post.call_args.kwargs["json"])

    @patch("services.llm_service.requests.post")
    def test_invalid_openai_candidate_shape_uses_three_local_candidates(self, post):
        post.return_value = chat_response('{"candidates":[{"molecule":"missing fields"}]}')
        service = LLMService(api_key="test-key")

        candidates = service.generate_novel_candidates("HZSM_5")

        self.assertEqual(len(candidates), 3)
        self.assertEqual(service.last_source, "local-fallback")
        self.assertTrue(all(item["generation_source"] == "local-fallback" for item in candidates))

    @patch("services.llm_service.requests.post")
    def test_openai_error_is_sanitized(self, post):
        post.return_value = FakeResponse(401, {"error": {"message": "sensitive upstream detail"}})
        service = LLMService(api_key="test-key")

        result = service.compound_analysis({"molecule": "HZSM_5"})

        self.assertIsNone(result)
        self.assertNotIn("sensitive", service.last_error)
        self.assertIn("credentials", service.last_error)


class DatabaseServiceTests(unittest.TestCase):
    @patch("services.database_service.requests.get")
    def test_synonym_404_does_not_discard_valid_properties(self, get):
        get.side_effect = [
            FakeResponse(200, {
                "PropertyTable": {"Properties": [{
                    "CID": 1,
                    "MolecularFormula": "CH4",
                    "MolecularWeight": "16.04",
                    "SMILES": "C",
                    "ConnectivitySMILES": "C",
                }]},
            }),
            FakeResponse(404, {"Fault": {"Message": "No synonyms"}}),
        ]

        compound = DatabaseService().fetch_pubchem("methane/test")

        self.assertEqual(compound.cid, 1)
        self.assertEqual(compound.synonyms, [])
        self.assertEqual(compound.isomeric_smiles, "C")
        self.assertEqual(compound.connectivity_smiles, "C")
        self.assertEqual(compound.source_url, "https://pubchem.ncbi.nlm.nih.gov/compound/1")
        self.assertIn("methane%2Ftest", get.call_args_list[0].args[0])


class FeedbackServiceTests(unittest.TestCase):
    def test_feedback_requires_finite_unit_interval_measurements(self):
        with tempfile.TemporaryDirectory() as directory:
            service = FeedbackService(Path(directory) / "logs.jsonl")
            invalid_payloads = [
                {},
                {"molecule": "HZSM_5"},
                {"molecule": "HZSM_5", "actual_activity": math.nan},
                {"molecule": "HZSM_5", "actual_activity": 1.1},
            ]
            for payload in invalid_payloads:
                with self.subTest(payload=payload), self.assertRaises(InvalidInputError):
                    service.log_experiment(payload)

    def test_feedback_round_trip_is_bounded_and_typed(self):
        with tempfile.TemporaryDirectory() as directory:
            service = FeedbackService(Path(directory) / "logs.jsonl")
            entry = service.log_experiment({
                "molecule": " HZSM_5 ",
                "actual_activity": 0.9,
                "actual_selectivity": 0.8,
            })

            self.assertEqual(entry["payload"]["molecule"], "HZSM_5")
            self.assertEqual(service.get_all_logs(), [entry])


class KnowledgeAndAnalysisTests(unittest.TestCase):
    def test_unknown_knowledge_reference_is_rejected(self):
        fixture = Path(__file__).parent / "fixtures" / "bad_reference.metta"
        with self.assertRaises(KnowledgeBaseError):
            MeTTaKnowledgeBase(fixture)

    def test_non_finite_agent_ranking_value_is_rejected(self):
        props = MoleculeProperties(
            molecular_weight=1.0,
            formula="X",
            categories=[],
            targets=[],
            functional_groups=[],
            activity_score=math.nan,
            selectivity=0.5,
            stability_h=1.0,
        )
        discovery = DiscoveryResult(
            query={},
            count=1,
            candidates=[CandidateCompound("Bad", props)],
        )

        with self.assertRaises(InvalidInputError):
            AnalysisService().rank(discovery)


if __name__ == "__main__":
    unittest.main()
