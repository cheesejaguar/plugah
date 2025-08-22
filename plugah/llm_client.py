"""
LLM client abstraction and a default LiteLLM-backed implementation.
This avoids importing provider SDKs. It targets LiteLLM's OpenAI-compatible API.
"""

from __future__ import annotations

import json
import os
from typing import Any, Protocol

import httpx


class LLMClient(Protocol):
    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
    ) -> str:  # pragma: no cover - interface
        ...


class LiteLLMClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        default_model: str | None = None,
        extra_headers_json: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("LITELLM_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("LITELLM_API_KEY", "")
        self.default_model = default_model or os.getenv("LITELLM_MODEL", "route.default")
        self._client = client or httpx.Client(timeout=30)
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        extra = extra_headers_json or os.getenv("LITELLM_HEADERS_JSON")
        if extra:
            try:
                parsed = json.loads(extra)
                if isinstance(parsed, dict):
                    headers.update({str(k): str(v) for k, v in parsed.items()})
            except Exception:
                pass
        self._headers = headers

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
    ) -> str:
        if not self.base_url:
            content = "\n".join(m.get("content", "") for m in messages if m.get("role") == "user")
            return content.strip() or ""

        url = f"{self.base_url}/v1/chat/completions"
        payload: dict[str, Any] = {"model": model or self.default_model, "messages": messages}
        if temperature is not None:
            payload["temperature"] = temperature
        try:
            resp = self._client.post(url, headers=self._headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
        except Exception as e:
            user_text = "\n".join(
                m.get("content", "") for m in messages if m.get("role") == "user"
            )
            return user_text.strip() or f"[LLM error: {e}]"

