"""PubChem lookup service."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from exceptions import ExternalAPIError, ExternalNotFoundError, InvalidInputError
from models.molecule import PubChemCompound
from services.base_service import BioAgentService, ServiceIdentity


class DatabaseService(BioAgentService):
    identity = ServiceIdentity("DatabaseAgent", "db_agent_secret", 8003)

    _BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"
    _PROPERTIES = (
        "MolecularFormula,MolecularWeight,IUPACName,IsomericSMILES,XLogP,Charge"
    )

    def __init__(self, *, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def fetch_pubchem(self, query: str) -> PubChemCompound:
        cleaned = query.strip() if isinstance(query, str) else ""
        if not cleaned:
            raise InvalidInputError("PubChem lookup query must be a non-empty string.")

        slug = quote(cleaned)
        payload = self._get_json(f"{self._BASE_URL}/{slug}/property/{self._PROPERTIES}/JSON")
        rows = payload.get("PropertyTable", {}).get("Properties", [])
        if not rows:
            raise ExternalNotFoundError(f"PubChem did not return properties for '{cleaned}'.")

        row = rows[0]
        synonyms = self._fetch_synonyms(slug)
        cid_raw = row.get("CID")
        if cid_raw is None:
             raise ExternalAPIError("PubChem returned properties but missing CID.")
             
        return PubChemCompound(
            cid=int(cid_raw),
            iupac_name=row.get("IUPACName"),
            molecular_formula=row.get("MolecularFormula"),
            molecular_weight=self._float_or_none(row.get("MolecularWeight")),
            isomeric_smiles=row.get("IsomericSMILES"),
            xlogp=self._float_or_none(row.get("XLogP")),
            charge=self._int_or_none(row.get("Charge")),
            synonyms=synonyms,
        )

    def _fetch_synonyms(self, slug: str) -> list[str]:
        try:
            payload = self._get_json(f"{self._BASE_URL}/{slug}/synonyms/JSON")
        except ExternalAPIError:
            return []
        infos = payload.get("InformationList", {}).get("Information", [])
        if not infos:
            return []
        synonyms = infos[0].get("Synonym", [])
        return [str(item) for item in synonyms[:10]]

    def _get_json(self, url: str) -> dict[str, Any]:
        try:
            response = requests.get(url, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ExternalAPIError(f"PubChem request failed: {exc}") from exc
        if response.status_code == 404:
            raise ExternalNotFoundError("PubChem did not find a matching compound.")
        if response.status_code >= 400:
            raise ExternalAPIError(f"PubChem returned HTTP {response.status_code}: {response.text[:200]}")
        try:
            return response.json()
        except ValueError as exc:
            raise ExternalAPIError("PubChem returned invalid JSON.") from exc

    @staticmethod
    def _float_or_none(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _int_or_none(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
