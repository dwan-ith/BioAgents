from __future__ import annotations

import importlib
import os
import unittest


class BioAgentsApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.pop("OPENAI_API_KEY", None)
        cls.server = importlib.import_module("server")
        cls.client = cls.server.app.test_client()

    def test_health_reports_local_fallback_without_openai_key(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "healthy")
        self.assertEqual(payload["mode"], "local-fallback")
        self.assertFalse(payload["openai_available"])

    def test_vercel_api_prefix_routes_to_flask_app(self):
        health = self.client.get("/api/health")
        query = self.client.post("/api/query", json={
            "type": "compound",
            "molecule": "HZSM_5",
        })

        self.assertEqual(health.status_code, 200)
        self.assertEqual(query.status_code, 200)
        self.assertEqual(query.get_json()["molecule"], "HZSM_5")

    def test_compound_query_uses_local_knowledge_base(self):
        response = self.client.post("/query", json={
            "type": "compound",
            "molecule": "Cu_ZnO_Al2O3",
        })

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["molecule"], "Cu_ZnO_Al2O3")
        self.assertEqual(payload["mode"], "local-fallback")
        self.assertIn("chemical_catalyst", payload["properties"]["categories"])

    def test_unknown_molecule_returns_domain_404(self):
        response = self.client.post("/query", json={
            "type": "compound",
            "molecule": "NotARealCatalyst",
        })

        self.assertEqual(response.status_code, 404)
        payload = response.get_json()
        self.assertEqual(payload["error_type"], "MoleculeNotFoundError")

    def test_discovery_ranks_candidates(self):
        response = self.client.post("/query", json={
            "type": "discover",
            "target_class": "enzyme",
            "criterion": "selectivity",
            "order": "desc",
        })

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["mode"], "local-fallback")
        self.assertGreater(payload["research"]["count"], 0)
        self.assertEqual(payload["analysis"]["criterion"], "selectivity")
        self.assertGreater(len(payload["analysis"]["ranked_candidates"]), 0)

    def test_generate_has_local_fallback_candidates(self):
        response = self.client.post("/query", json={
            "type": "generate",
            "molecule": "HZSM_5",
        })

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["mode"], "local-fallback")
        self.assertFalse(payload["llm_available"])
        self.assertGreater(len(payload["novel_candidates"]), 0)


if __name__ == "__main__":
    unittest.main()
