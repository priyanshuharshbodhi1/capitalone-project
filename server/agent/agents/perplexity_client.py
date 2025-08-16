import json
import logging
from typing import Any, Dict, List, Optional
import requests

from ...infra.settings import settings  # type: ignore
from pathlib import Path
# Note: RAG is the primary approach in this system. This Perplexity client acts as a
# live web helper for scheme lookups; when unavailable, the agent falls back to RAG.
try:
    from ..prompts.perplexity_govt_policy import PERPLEXITY_GOVT_POLICY_SYSTEM_PROMPT
except Exception:  # fallback if module not available for any reason
    PERPLEXITY_GOVT_POLICY_SYSTEM_PROMPT = None

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


class PerplexityClient:
    """Thin client around Perplexity Chat Completions API.

    Returns a normalized structure compatible with our GovtPolicyAgent expectations.
    """

    def __init__(self, api_key: Optional[str]) -> None:
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _load_system_prompt(self) -> str:
        # Prefer Python prompt module for consistency with other prompts
        if PERPLEXITY_GOVT_POLICY_SYSTEM_PROMPT:
            return PERPLEXITY_GOVT_POLICY_SYSTEM_PROMPT
        # Fallback to text file if present
        try:
            base = Path(__file__).resolve().parents[1] / "prompts" / "perplexity_govt_policy_prompt.txt"
            return base.read_text(encoding="utf-8")
        except Exception:
            # Safe minimal fallback
            return (
                "You are an expert Indian agriculture policy assistant. Return STRICT JSON only with a 'schemes' array and 'recommendations'."
            )

    def _build_prompt(self, query: str, state: Optional[str], farmer_type: Optional[str]) -> List[Dict[str, Any]]:
        system = self._load_system_prompt()
        if state:
            system += f" The farmer is from the state of {state}."
        if farmer_type:
            system += f" The farmer type is {farmer_type}."

        user = (
            f"Question: {query}\n\n"
            "Return ONLY JSON with this shape (no markdown):\n"
            "{\n"
            "  \"schemes\": [\n"
            "    {\n"
            "      \"name\": string,\n"
            "      \"description\": string,\n"
            "      \"eligibility\": [string],\n"
            "      \"subsidy_amount\": string,\n"
            "      \"required_documents\": [string],\n"
            "      \"application_links\": [string],\n"
            "      \"state\": string | null,\n"
            "      \"implementing_agency\": string | null,\n"
            "      \"source_url\": string | null\n"
            "    }\n"
            "  ],\n"
            "  \"recommendations\": [string]\n"
            "}\n"
            "Limit to at most 5 schemes. If unsure, still attempt to provide the best available official links."
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    def search_schemes(self, query: str, state: Optional[str], farmer_type: Optional[str]) -> Dict[str, Any]:
        if not self.available:
            return {"success": False, "error": "Perplexity API key not configured"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "sonar-reasoning-pro",
            "messages": self._build_prompt(query, state, farmer_type),
            "temperature": 0.2,
            "max_tokens": 1200,
        }

        try:
            resp = requests.post(PERPLEXITY_API_URL, headers=headers, data=json.dumps(payload), timeout=30)
            resp.raise_for_status()
            data = resp.json()

            # Perplexity returns OpenAI-compatible choices
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            parsed = self._parse_json_safe(content)
            if not parsed:
                # Retry once with a stricter reminder
                payload_retry = dict(payload)
                payload_retry["messages"] = payload["messages"] + [
                    {"role": "system", "content": "Return STRICT JSON only. No markdown fences. No prose."}
                ]
                resp = requests.post(PERPLEXITY_API_URL, headers=headers, data=json.dumps(payload_retry), timeout=30)
                resp.raise_for_status()
                data = resp.json()
                content = (
                    data.get("choices", [{}])[0].get("message", {}).get("content", "")
                )
                parsed = self._parse_json_safe(content)
                if not parsed:
                    return {"success": False, "error": "Perplexity returned non-JSON response"}

            schemes = parsed.get("schemes", []) or []
            recommendations = parsed.get("recommendations", []) or []
            schemes = schemes[:5]

            # Normalize to GovtPolicyAgent format
            return {
                "success": True,
                "schemes": schemes,
                "farmer_recommendations": recommendations,
                "total_found": len(schemes),
                "confidence": 0.85,  # heuristic
                "raw": content,
            }
        except Exception as e:
            self.logger.error(f"Perplexity search error: {e}")
            return {"success": False, "error": str(e)}

    def _parse_json_safe(self, text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        # Try direct JSON
        try:
            return json.loads(text)
        except Exception:
            pass
        # Try to find fenced JSON block
        import re

        m = re.search(r"```(?:json)?\n(.*?)\n```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                return None
        return None
