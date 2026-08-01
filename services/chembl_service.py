"""Bounded ChEMBL evidence retrieval with explicit provenance."""

from __future__ import annotations

import time
from threading import RLock
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from exceptions import ExternalAPIError, InvalidInputError
from services.base_service import BioAgentService, ServiceIdentity


class ChEMBLService(BioAgentService):
    identity = ServiceIdentity("EvidenceAgent", "ChEMBL bioactivity evidence", "/api/workflows/discovery")

    _BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"
    _CACHE_TTL_SECONDS = 15 * 60

    def __init__(self, *, timeout: float = 8.0) -> None:
        if timeout <= 0:
            raise ValueError("ChEMBL timeout must be greater than zero.")
        self.timeout = timeout
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._cache_lock = RLock()
        self._session = requests.Session()
        retries = Retry(
            total=1,
            backoff_factor=0.35,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
        )
        self._session.mount("https://", HTTPAdapter(max_retries=retries))
        self._session.headers.update({"User-Agent": "BioAgents/2.0 evidence-client"})

    def evidence_for_inchikey(self, inchikey: str, *, activity_limit: int = 50) -> dict[str, Any]:
        cleaned = inchikey.strip().upper() if isinstance(inchikey, str) else ""
        if len(cleaned) != 27:
            raise InvalidInputError("A standard 27-character InChIKey is required for ChEMBL lookup.")
        if not 1 <= activity_limit <= 100:
            raise InvalidInputError("ChEMBL activity limit must be between 1 and 100.")

        molecule_payload = self._get_json(
            "/molecule.json",
            params={"molecule_structures__standard_inchi_key": cleaned, "limit": 1},
        )
        molecules = molecule_payload.get("molecules") or []
        if not molecules:
            return {
                "status": "NO_CHEMBL_MATCH",
                "inchikey": cleaned,
                "molecule": None,
                "targets": [],
                "activities": [],
                "provenance": [self._molecule_source(cleaned)],
            }

        molecule = molecules[0]
        chembl_id = molecule.get("molecule_chembl_id")
        if not isinstance(chembl_id, str) or not chembl_id:
            raise ExternalAPIError("ChEMBL molecule response omitted molecule_chembl_id.")

        activity_payload = self._get_json(
            "/activity.json",
            params={
                "molecule_chembl_id": chembl_id,
                "pchembl_value__isnull": "false",
                "limit": activity_limit,
                "order_by": "-pchembl_value",
            },
        )
        activities = self._normalize_activities(activity_payload.get("activities") or [])
        targets = self._summarize_targets(activities)
        properties = molecule.get("molecule_properties") or {}
        return {
            "status": "EVIDENCE_FOUND",
            "inchikey": cleaned,
            "molecule": {
                "chembl_id": chembl_id,
                "preferred_name": molecule.get("pref_name"),
                "molecule_type": molecule.get("molecule_type"),
                "max_phase": molecule.get("max_phase"),
                "therapeutic_flag": molecule.get("therapeutic_flag"),
                "first_approval": molecule.get("first_approval"),
                "withdrawn_flag": molecule.get("withdrawn_flag"),
                "qed": self._number(properties.get("qed_weighted")),
                "rule_of_five_violations": self._integer(properties.get("num_ro5_violations")),
            },
            "targets": targets,
            "activities": activities[:20],
            "activity_count_returned": len(activities),
            "evidence_grade": self._evidence_grade(activities, targets),
            "provenance": [
                self._molecule_source(cleaned),
                {
                    "provider": "ChEMBL",
                    "resource": "bioactivity records",
                    "url": f"{self._BASE_URL}/activity.json?molecule_chembl_id={chembl_id}",
                    "retrieved_live": True,
                },
            ],
            "limitations": [
                "Assay records are heterogeneous and are not directly comparable without protocol review.",
                "pChEMBL values summarize potency only for supported standard relation/type/unit records.",
                "Database presence or target activity does not establish clinical efficacy or safety.",
            ],
        }

    def unavailable_evidence(self, inchikey: str, reason: str) -> dict[str, Any]:
        return {
            "status": "EVIDENCE_UNAVAILABLE",
            "inchikey": inchikey,
            "molecule": None,
            "targets": [],
            "activities": [],
            "evidence_grade": "NONE",
            "reason": reason,
            "provenance": [self._molecule_source(inchikey)],
        }

    def _get_json(self, path: str, *, params: dict[str, Any]) -> dict[str, Any]:
        cache_key = requests.Request("GET", f"{self._BASE_URL}{path}", params=params).prepare().url
        assert cache_key is not None
        with self._cache_lock:
            cached = self._cache.get(cache_key)
            if cached and time.monotonic() - cached[0] < self._CACHE_TTL_SECONDS:
                return cached[1]

        try:
            response = self._session.get(
                f"{self._BASE_URL}{path}",
                params=params,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ExternalAPIError("ChEMBL evidence service is temporarily unreachable.") from exc
        if response.status_code >= 400:
            raise ExternalAPIError(f"ChEMBL returned HTTP {response.status_code}.")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ExternalAPIError("ChEMBL returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise ExternalAPIError("ChEMBL returned an unexpected response shape.")
        with self._cache_lock:
            if len(self._cache) >= 256:
                oldest = min(self._cache, key=lambda key: self._cache[key][0])
                self._cache.pop(oldest, None)
            self._cache[cache_key] = (time.monotonic(), payload)
        return payload

    @classmethod
    def _normalize_activities(cls, rows: list[Any]) -> list[dict[str, Any]]:
        normalized = []
        for row in rows:
            if not isinstance(row, dict) or row.get("data_validity_comment"):
                continue
            pchembl = cls._number(row.get("pchembl_value"))
            target_id = row.get("target_chembl_id")
            if pchembl is None or not isinstance(target_id, str):
                continue
            normalized.append({
                "target_chembl_id": target_id,
                "target_name": row.get("target_pref_name") or "Unspecified target",
                "organism": row.get("target_organism"),
                "assay_chembl_id": row.get("assay_chembl_id"),
                "document_chembl_id": row.get("document_chembl_id"),
                "standard_type": row.get("standard_type"),
                "assay_type": row.get("assay_type"),
                "standard_relation": row.get("standard_relation"),
                "standard_value": cls._number(row.get("standard_value")),
                "standard_units": row.get("standard_units"),
                "pchembl_value": pchembl,
                "source_url": f"https://www.ebi.ac.uk/chembl/explore/compound/{row.get('molecule_chembl_id')}",
            })
        normalized.sort(key=lambda item: item["pchembl_value"], reverse=True)
        return normalized

    @staticmethod
    def _summarize_targets(activities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for activity in activities:
            target_id = activity["target_chembl_id"]
            target = grouped.setdefault(target_id, {
                "target_chembl_id": target_id,
                "target_name": activity["target_name"],
                "organism": activity["organism"],
                "measurement_count": 0,
                "max_pchembl_value": activity["pchembl_value"],
                "assay_types": set(),
            })
            target["measurement_count"] += 1
            target["max_pchembl_value"] = max(target["max_pchembl_value"], activity["pchembl_value"])
            if activity["standard_type"]:
                target["assay_types"].add(activity["standard_type"])
        results = []
        for target in grouped.values():
            target["max_pchembl_value"] = round(target["max_pchembl_value"], 2)
            target["assay_types"] = sorted(target["assay_types"])
            results.append(target)
        results.sort(key=lambda item: (item["max_pchembl_value"], item["measurement_count"]), reverse=True)
        return results[:20]

    @staticmethod
    def _evidence_grade(activities: list[dict[str, Any]], targets: list[dict[str, Any]]) -> str:
        human_exact = [
            activity
            for activity in activities
            if activity.get("organism") == "Homo sapiens"
            and activity.get("standard_relation") == "="
            and activity.get("target_name") not in {None, "Unchecked", "Unspecified target"}
        ]
        distinct_documents = {activity.get("document_chembl_id") for activity in human_exact if activity.get("document_chembl_id")}
        if len(human_exact) >= 3 and len(distinct_documents) >= 2 and len(targets) >= 1:
            return "MODERATE"
        if activities:
            return "LIMITED"
        return "NONE"

    @classmethod
    def _molecule_source(cls, inchikey: str) -> dict[str, Any]:
        return {
            "provider": "ChEMBL",
            "resource": "molecule by standard InChIKey",
            "url": f"{cls._BASE_URL}/molecule.json?molecule_structures__standard_inchi_key={inchikey}",
            "retrieved_live": True,
        }

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if number == number and abs(number) != float("inf") else None

    @classmethod
    def _integer(cls, value: Any) -> int | None:
        number = cls._number(value)
        return int(number) if number is not None else None
