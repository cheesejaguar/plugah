"""
Thin OpenAI client wrapper for reasoning/decision-making calls.

Usage:
    from .llm import LLM
    text = LLM().reason(model="gpt-5-nano", system="...", user="...")
"""

from __future__ import annotations


class LLM:
    def __init__(self, model: str | None = None, temperature: float = 0.2):
        import os

        self.model = model or os.getenv(
            "OPENAI_MODEL", os.getenv("DEFAULT_LLM_MODEL", "gpt-5-nano")
        )
        self.temperature = temperature

    def _has_openai(self) -> bool:
        try:
            import openai  # noqa: F401

            return True
        except Exception:
            return False

    def reason(
        self, system: str, user: str, *, model: str | None = None, temperature: float | None = None
    ) -> str | None:
        """Call OpenAI Chat Completions API and return the assistant text.

        Returns None if the SDK is not available or the API call fails.
        """
        if not self._has_openai():
            return None

        try:
            from openai import OpenAI

            client = OpenAI()
            resp = client.chat.completions.create(
                model=model or self.model,
                temperature=temperature if temperature is not None else self.temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )

            choice = resp.choices[0]
            return choice.message.content or ""
        except Exception:
            return None
