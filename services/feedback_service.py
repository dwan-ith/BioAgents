"""Experiment feedback log service."""

from __future__ import annotations

import json
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
        entry = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
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
