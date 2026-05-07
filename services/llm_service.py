"""OpenAI-primary LLM service with deterministic local fallback."""

from __future__ import annotations

import json
import os
from typing import Any

import requests

from knowledge.metta_handler import get_kb
from services.base_service import BioAgentService, ServiceIdentity


class LLMService(BioAgentService):
    identity = ServiceIdentity("LLMAgent", "llm_agent_secret", 8007)

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
        self.timeout = timeout
        self.last_error: str | None = None
        self.last_source = "openai-primary" if self.api_key else "local-fallback"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    def compound_analysis(self, profile: dict[str, Any]) -> dict[str, Any] | None:
        prompt = (
            "Analyze this catalyst or enzyme profile for synthetic biology use. "
            "Return JSON with keys: summary, strengths, risks, next_experiments."
        )
        result = self._json_response(prompt, profile)
        return result if isinstance(result, dict) else None

    def interaction_analysis(self, report: dict[str, Any]) -> dict[str, Any] | None:
        prompt = (
            "Analyze this interaction report. Return JSON with keys: summary, "
            "risk_interpretation, mitigation_steps, validation_tests."
        )
        result = self._json_response(prompt, report)
        return result if isinstance(result, dict) else None

    def discovery_analysis(
        self,
        research: dict[str, Any],
        analysis: dict[str, Any],
    ) -> dict[str, Any] | None:
        prompt = (
            "Review these discovery and ranking results. Return JSON with keys: "
            "summary, ranked_molecules, recommendation, caveats. ranked_molecules "
            "must be an array of objects with molecule and rationale."
        )
        result = self._json_response(prompt, {"research": research, "analysis": analysis})
        return result if isinstance(result, dict) else None

    def generate_insight(self, context_type: str, data: dict[str, Any]) -> str | None:
        prompt = (
            f"Write a concise technical insight for this {context_type}. "
            "Do not invent facts beyond the supplied data."
        )
        result = self._text_response(prompt, data)
        if result:
            return result
        return self._local_insight(context_type, data)

    def generate_novel_candidates(self, base_molecule: str) -> list[dict[str, Any]]:
        kb = get_kb()
        canonical = kb.resolve_name(base_molecule)
        prompt = (
            "Propose three plausible catalyst/enzyme optimization candidates based "
            "on the supplied molecule name and local knowledge. Return JSON array "
            "objects with keys: molecule, modification, rationale, expected_effect."
        )
        result = self._json_response(prompt, {"base_molecule": canonical})
        if isinstance(result, list):
            self.last_source = "openai-primary"
            return result
        if isinstance(result, dict) and isinstance(result.get("candidates"), list):
            self.last_source = "openai-primary"
            return result["candidates"]
        self.last_source = "local-fallback"
        if self.last_error is None and not self.api_key:
            self.last_error = "OPENAI_API_KEY is not set."
        return self._local_candidates(canonical)

    def _json_response(self, prompt: str, data: dict[str, Any]) -> dict[str, Any] | list[dict[str, Any]] | None:
        text = self._text_response(prompt + " Respond with JSON only.", data)
        if not text:
            return None
        try:
            return json.loads(self._strip_code_fence(text))
        except json.JSONDecodeError:
            self.last_error = "OpenAI response was not valid JSON."
            self.last_source = "local-fallback"
            return None

    def _text_response(self, prompt: str, data: dict[str, Any]) -> str | None:
        if not self.api_key:
            self.last_error = "OPENAI_API_KEY is not set."
            self.last_source = "local-fallback"
            return None

        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are BioAgents, a careful assistant for catalyst, enzyme, "
                        "and synthetic biology screening. Be concise and uncertainty-aware. "
                        "Always respond with valid JSON if requested."
                    ),
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\nData:\n{json.dumps(data, sort_keys=True)}",
                },
            ],
            "response_format": {"type": "json_object"} if "JSON" in prompt else None
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=body,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            self.last_error = f"OpenAI request failed: {exc}"
            self.last_source = "local-fallback"
            return None

        if response.status_code >= 400:
            self.last_error = f"OpenAI returned HTTP {response.status_code}: {response.text[:300]}"
            self.last_source = "local-fallback"
            return None

        try:
            payload = response.json()
        except ValueError:
            self.last_error = "OpenAI returned invalid JSON."
            self.last_source = "local-fallback"
            return None

        text = self._extract_response_text(payload)
        if not text:
            self.last_error = "OpenAI response did not contain text output."
            self.last_source = "local-fallback"
            return None

        self.last_error = None
        self.last_source = "openai-primary"
        return text

    @staticmethod
    def _extract_response_text(payload: dict[str, Any]) -> str:
        # Chat Completions standard
        choices = payload.get("choices", [])
        if choices and isinstance(choices, list):
            message = choices[0].get("message", {})
            if isinstance(message, dict) and message.get("content"):
                return message["content"].strip()

        # Fallback for alternative/legacy formats
        if isinstance(payload.get("output_text"), str):
            return payload["output_text"].strip()
        
        chunks = []
        for item in payload.get("output", []):
            if not isinstance(item, dict):
                continue
            for content in item.get("content", []):
                if not isinstance(content, dict):
                    continue
                if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                    chunks.append(content["text"])
        return "\n".join(chunks).strip()

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if len(lines) >= 3:
                return "\n".join(lines[1:-1]).strip()
        return stripped

    @staticmethod
    def _local_insight(context_type: str, data: dict[str, Any]) -> str:
        if context_type == "compound profile":
            molecule = data.get("molecule", "This molecule")
            props = data.get("properties", {})
            categories = ", ".join(props.get("categories") or ["uncategorized"])
            return (
                f"{molecule} is locally classified as {categories}; prioritize validation "
                "against the listed activity, selectivity, and stability signals."
            )
        if context_type == "drug interaction":
            return f"Local rules estimate {data.get('risk_level', 'unknown')} risk for this pair."
        return "Local ranking is based on knowledge-base activity, selectivity, and stability fields."

    @staticmethod
    def _local_candidates(base_molecule: str) -> list[dict[str, Any]]:
        kb = get_kb()
        props = kb.get_properties(base_molecule)
        similar = kb.get_similar(base_molecule)
        candidates = []
        for index, neighbor in enumerate(similar[:2], start=1):
            candidates.append({
                "molecule": f"{base_molecule}_hybrid_{index}",
                "modification": f"Borrow support or active-site features from {neighbor}.",
                "rationale": "Generated by local fallback using similarity relationships in the KB.",
                "expected_effect": "Potentially preserve core function while testing nearby design space.",
                "generation_source": "local-fallback",
            })
        if len(candidates) < 3:
            categories = props.categories[:2] or ["process"]
            candidates.append({
                "molecule": f"{base_molecule}_stability_variant",
                "modification": "Tune support, immobilization, or operating window for stability.",
                "rationale": f"Local profile tags this compound as {', '.join(categories)}.",
                "expected_effect": "Improved lifetime with activity/selectivity measured experimentally.",
                "generation_source": "local-fallback",
            })
        return candidates[:3]
