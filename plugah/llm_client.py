"""
LLM client abstraction and a default LiteLLM-backed implementation.
This avoids importing provider SDKs. It targets LiteLLM's OpenAI-compatible API.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Protocol

import httpx


class LLMClient(Protocol):
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:  # pragma: no cover - interface
        ...


class LiteLLMClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        extra_headers_json: Optional[str] = None,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("LITELLM_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("LITELLM_API_KEY", "")
        self.default_model = default_model or os.getenv("LITELLM_MODEL", "route.default")
        self._client = client or httpx.Client(timeout=30)
        headers: Dict[str, str] = {"Content-Type": "application/json"}
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
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        if not self.base_url:
            content = "\n".join(m.get("content", "") for m in messages if m.get("role") == "user")
            return content.strip() or ""

        url = f"{self.base_url}/v1/chat/completions"
        payload: Dict[str, Any] = {"model": model or self.default_model, "messages": messages}
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

