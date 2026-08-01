"""Experiment feedback log service."""

from __future__ import annotations

import json
import math
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from exceptions import InvalidInputError
from services.base_service import BioAgentService, ServiceIdentity


class FeedbackService(BioAgentService):
    identity = ServiceIdentity("FeedbackAgent", "feedback_agent_secret", 8008)

    def __init__(self, path: str | Path | None = None) -> None:
        configured = path or os.getenv("BIOAGENTS_FEEDBACK_LOG")
        if configured:
            self.path = Path(configured)
        elif os.getenv("VERCEL"):
            self.path = Path(tempfile.gettempdir()) / "bioagents_experiment_logs.jsonl"
        else:
            self.path = Path("data") / "experiment_logs.jsonl"

    def log_experiment(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise InvalidInputError("Experiment payload must be a JSON object.")
        molecule = payload.get("molecule")
        if not isinstance(molecule, str) or not molecule.strip():
            raise InvalidInputError("Field 'molecule' must be a non-empty string.")

        normalized = dict(payload)
        normalized["molecule"] = molecule.strip()
        normalized["actual_activity"] = self._unit_interval(
            payload.get("actual_activity"), "actual_activity", required=True
        )
        if "actual_selectivity" in payload:
            normalized["actual_selectivity"] = self._unit_interval(
                payload.get("actual_selectivity"), "actual_selectivity", required=False
            )
        entry = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": normalized,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def get_all_logs(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        logs = []
        with open(self.path, encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    logs.append(json.loads(stripped))
                except json.JSONDecodeError:
                    continue
        return logs

    @staticmethod
    def _unit_interval(value: Any, field: str, *, required: bool) -> float | None:
        if value is None:
            if required:
                raise InvalidInputError(f"Field '{field}' is required.")
            return None
        if isinstance(value, bool):
            raise InvalidInputError(f"Field '{field}' must be a finite number between 0 and 1.")
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise InvalidInputError(
                f"Field '{field}' must be a finite number between 0 and 1."
            ) from exc
        if not math.isfinite(number) or not 0.0 <= number <= 1.0:
            raise InvalidInputError(f"Field '{field}' must be between 0 and 1.")
        return number
