"""Validated configuration shared by the optional standalone uAgents runtime."""

from __future__ import annotations

import os
import warnings

from dotenv import load_dotenv

load_dotenv()


def agent_kwargs(slug: str, name: str, default_port: int) -> dict:
    prefix = f"BIOAGENTS_{slug.upper()}"
    port = _port(os.getenv(f"{prefix}_PORT"), default_port, f"{prefix}_PORT")
    seed = (os.getenv(f"{prefix}_SEED") or "").strip()
    if not seed:
        seed = f"bioagents-local-development-{slug}"
        warnings.warn(
            f"{prefix}_SEED is not set; using a public development identity. "
            "Set a private seed before registering or deploying this agent.",
            RuntimeWarning,
            stacklevel=2,
        )
    endpoint = (os.getenv(f"{prefix}_ENDPOINT") or f"http://127.0.0.1:{port}/submit").strip()
    return {
        "name": name,
        "seed": seed,
        "port": port,
        "endpoint": [endpoint],
    }


def bureau_kwargs() -> dict:
    port = _port(os.getenv("BIOAGENTS_BUREAU_PORT"), 8000, "BIOAGENTS_BUREAU_PORT")
    endpoint = (
        os.getenv("BIOAGENTS_BUREAU_ENDPOINT") or f"http://127.0.0.1:{port}/submit"
    ).strip()
    return {"port": port, "endpoint": [endpoint]}


def _port(raw: str | None, default: int, field: str) -> int:
    try:
        value = int(raw) if raw else default
    except ValueError as exc:
        raise RuntimeError(f"{field} must be an integer port number.") from exc
    if not 1 <= value <= 65535:
        raise RuntimeError(f"{field} must be between 1 and 65535.")
    return value
