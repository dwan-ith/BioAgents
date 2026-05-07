"""BioAgents Flask API server.

The default runtime is deliberately synchronous and local: Flask calls the
service layer directly, services raise domain exceptions, and this module is
only responsible for HTTP validation, routing, and JSON serialization.

The standalone uAgents in ``agents/`` are kept for distributed experiments,
but the dashboard and tests do not depend on a running Bureau.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from flask import Flask, g, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

from exceptions import BioAgentError, InvalidInputError
from services.analysis_service import AnalysisService
from services.compound_service import CompoundService
from services.database_service import DatabaseService
from services.feedback_service import FeedbackService
from services.llm_service import LLMService
from services.reaction_service import ReactionService
from services.research_service import ResearchService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)-28s] %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
CORS(app)
load_dotenv()

_compound = CompoundService()
_database = DatabaseService()
_reaction = ReactionService()
_research = ResearchService()
_analysis = AnalysisService()
_llm = LLMService()
_feedback = FeedbackService()

_all_services = [_compound, _database, _reaction, _research, _analysis, _llm, _feedback]


@app.before_request
def _start_timer() -> None:
    g.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    g.start_time = time.monotonic()
    logger.info("-> %s %s [%s]", request.method, request.path, g.request_id)


@app.after_request
def _attach_tracing_headers(response):
    duration_ms = (time.monotonic() - g.start_time) * 1000
    response.headers["X-Request-ID"] = g.request_id
    response.headers["X-Duration-Ms"] = f"{duration_ms:.1f}"
    logger.info(
        "<- %s %s [%s] %d %.1fms",
        request.method,
        request.path,
        g.request_id,
        response.status_code,
        duration_ms,
    )
    return response


@app.errorhandler(BioAgentError)
def _handle_service_error(exc: BioAgentError):
    logger.warning("Service error [%s]: %s", g.get("request_id"), exc.message)
    return jsonify({
        "error": exc.message,
        "error_type": type(exc).__name__,
        "request_id": g.get("request_id"),
    }), exc.http_status


@app.errorhandler(Exception)
def _handle_unexpected_error(exc: Exception):
    logger.exception("Unhandled exception [%s]", g.get("request_id"))
    return jsonify({
        "error": "An unexpected internal error occurred.",
        "error_type": "InternalError",
        "request_id": g.get("request_id"),
    }), 500


@app.get("/api/health")
@app.get("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "mode": "openai-primary" if _llm.is_available else "local-fallback",
        "openai_available": _llm.is_available,
        "openai_model": _llm.model if _llm.is_available else None,
    })


@app.get("/api/agents/status")
@app.get("/agents/status")
def agents_status():
    return jsonify({
        svc.name: {
            "address": svc.address,
            "endpoint": svc.endpoint,
            "status": "Ready",
            "mode": "openai-primary" if svc.name == "LLMAgent" and _llm.is_available else "local-fallback",
        }
        for svc in _all_services
    })


@app.get("/api/molecules")
@app.get("/molecules")
def molecules():
    graph = _compound.get_knowledge_graph()
    return jsonify(graph.to_dict())


@app.post("/api/query")
@app.post("/query")
def handle_query():
    body = _json_body()
    query_type = _string(body, "type", required=True)

    if query_type == "compound":
        molecule = _string(body, "molecule", required=True)
        profile = _compound.get_profile(molecule)
        result = profile.to_dict()
        _attach_compound_ai(result)
        return jsonify(result)

    if query_type == "lookup":
        query_str = _string(body, "query", required=True)
        compound = _database.fetch_pubchem(query_str)
        return jsonify(compound.to_dict())

    if query_type == "interaction":
        mol1 = _string(body, "mol1", required=True)
        mol2 = _string(body, "mol2", required=True)
        report = _reaction.simulate_reaction(mol1, mol2)
        result = report.to_dict()
        _attach_interaction_ai(result)
        return jsonify(result)

    if query_type == "discover":
        result = _run_discovery(body)
        _attach_discovery_ai(result)
        return jsonify(result)

    if query_type == "generate":
        molecule = _string(body, "molecule", required=True)
        base_profile = _compound.get_profile(molecule)
        candidates = _llm.generate_novel_candidates(base_profile.molecule)
        mode = _llm.last_source
        message = None if mode == "openai-primary" else _llm.last_error
        return jsonify({
            "base_molecule": base_profile.molecule,
            "novel_candidates": candidates,
            "llm_available": _llm.is_available,
            "mode": mode,
            "message": message,
        })

    raise InvalidInputError(
        f"Unknown query type: {query_type!r}. "
        "Expected one of: compound, lookup, interaction, discover, generate."
    )


@app.post("/api/experiments/log")
@app.post("/experiments/log")
def log_experiment():
    entry = _feedback.log_experiment(_json_body())
    return jsonify(entry), 201


@app.get("/api/experiments/logs")
@app.get("/experiments/logs")
def get_experiment_logs():
    return jsonify({"logs": _feedback.get_all_logs()})


def _run_discovery(body: dict[str, Any]) -> dict[str, Any]:
    target_class = _optional_string(body, "target_class")
    similar_to = _optional_string(body, "similar_to")
    min_activity = _optional_float(body, "min_activity")
    min_selectivity = _optional_float(body, "min_selectivity")
    criterion = _optional_string(body, "criterion") or "activity_score"
    order = (_optional_string(body, "order") or "desc").lower()

    if order not in {"asc", "desc"}:
        raise InvalidInputError("Field 'order' must be either 'asc' or 'desc'.")

    if (
        target_class is None
        and similar_to is None
        and min_activity is None
        and min_selectivity is None
    ):
        raise InvalidInputError(
            "Provide at least one filter: 'target_class', 'similar_to', "
            "'min_activity', or 'min_selectivity'."
        )

    discovery = _research.discover(
        target_class=target_class,
        similar_to=similar_to,
        min_activity=min_activity,
        min_selectivity=min_selectivity,
    )

    if discovery.count == 0:
        return {
            "message": "No compounds matched the supplied criteria.",
            "research": discovery.to_dict(),
            "analysis": None,
        }

    ranked = _analysis.rank(discovery, criterion=criterion, ascending=(order == "asc"))
    return {
        "research": discovery.to_dict(),
        "analysis": ranked.to_dict(),
    }


def _json_body() -> dict[str, Any]:
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise InvalidInputError("Request body must be a JSON object.")
    return body


def _string(body: dict[str, Any], field: str, *, required: bool) -> str:
    value = body.get(field)
    if value is None:
        if required:
            raise InvalidInputError(f"Field '{field}' is required.")
        return ""
    if not isinstance(value, str):
        raise InvalidInputError(f"Field '{field}' must be a string.")
    cleaned = value.strip()
    if required and not cleaned:
        raise InvalidInputError(f"Field '{field}' is required and must be non-empty.")
    return cleaned


def _optional_string(body: dict[str, Any], field: str) -> str | None:
    value = _string(body, field, required=False)
    return value or None


def _optional_float(body: dict[str, Any], field: str) -> float | None:
    raw = body.get(field)
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        raise InvalidInputError(f"Field '{field}' must be numeric.")


def _attach_compound_ai(result: dict[str, Any]) -> None:
    if not _llm.is_available:
        result["mode"] = "local-fallback"
        result["fallback_reason"] = "OPENAI_API_KEY is not set."
        return

    analysis = _llm.compound_analysis(result)
    if analysis:
        result["mode"] = "openai-primary"
        result["openai_model"] = _llm.model
        result["openai_analysis"] = analysis
    else:
        result["mode"] = "local-fallback"
        result["fallback_reason"] = _llm.last_error or "OpenAI analysis unavailable."


def _attach_interaction_ai(result: dict[str, Any]) -> None:
    if not _llm.is_available:
        result["mode"] = "local-fallback"
        result["fallback_reason"] = "OPENAI_API_KEY is not set."
        return

    analysis = _llm.interaction_analysis(result)
    if analysis:
        result["mode"] = "openai-primary"
        result["openai_model"] = _llm.model
        result["openai_analysis"] = analysis
    else:
        result["mode"] = "local-fallback"
        result["fallback_reason"] = _llm.last_error or "OpenAI analysis unavailable."


def _attach_discovery_ai(result: dict[str, Any]) -> None:
    if result.get("analysis") is None:
        result["mode"] = "local-fallback"
        result["fallback_reason"] = "No local candidates were available for OpenAI ranking."
        return
    if not _llm.is_available:
        result["mode"] = "local-fallback"
        result["fallback_reason"] = "OPENAI_API_KEY is not set."
        return

    analysis = _llm.discovery_analysis(result["research"], result["analysis"])
    if not analysis:
        result["mode"] = "local-fallback"
        result["fallback_reason"] = _llm.last_error or "OpenAI discovery analysis unavailable."
        return

    result["mode"] = "openai-primary"
    result["openai_model"] = _llm.model
    result["openai_analysis"] = analysis
    _reorder_ranked_candidates(result["analysis"], analysis)


def _reorder_ranked_candidates(local_analysis: dict[str, Any], openai_analysis: dict[str, Any]) -> None:
    ranked = local_analysis.get("ranked_candidates") or []
    by_name = {item.get("molecule"): item for item in ranked}
    rationales = {
        item.get("molecule"): item.get("rationale")
        for item in openai_analysis.get("ranked_molecules", [])
    }

    reordered = []
    seen = set()
    for item in openai_analysis.get("ranked_molecules", []):
        molecule = item.get("molecule")
        if molecule in by_name and molecule not in seen:
            candidate = dict(by_name[molecule])
            candidate["openai_rationale"] = rationales.get(molecule)
            reordered.append(candidate)
            seen.add(molecule)

    for item in ranked:
        molecule = item.get("molecule")
        if molecule not in seen:
            reordered.append(item)

    local_analysis["ranked_candidates"] = reordered
    local_analysis["ranking_source"] = "openai-primary"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
