from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Optional

from ..llm_client import LLMClient, LiteLLMClient


SLACK_RE = re.compile(r"slack\s+summarizer", re.I)


class DiscoveryEngine:
    def __init__(self, llm: Optional[LLMClient] = None) -> None:
        self.llm = llm or LiteLLMClient()

    def _seeded_questions(self, problem: str) -> List[str]:
        if SLACK_RE.search(problem or ""):
            return [
                "Which workspace and channels are in scope?",
                "What date range or period should we summarize?",
                "Any privacy or PII constraints to respect?",
                "Where should summaries be delivered (Slack/Drive/GitHub)?",
                "Preferred summary granularity (daily/weekly/incident)?",
                "Who are the target readers and decisions?",
            ]
        return []

    def generate_questions(self, problem: str, policy: str | None = None) -> List[str]:
        seeded = self._seeded_questions(problem)
        if seeded:
            return seeded[:6]

        prompt = [
            {"role": "system", "content": "Generate <=6 concise, non-overlapping discovery questions."},
            {"role": "user", "content": f"Problem: {problem}. Policy: {policy or 'balanced'}."},
        ]
        text = self.llm.chat(prompt, temperature=0.2)
        if not text:
            return [
                "Who are the primary users?",
                "Top 3 success criteria?",
                "Key constraints or integrations?",
                "Expected timeline?",
            ]
        # Split by lines/bullets
        lines = [re.sub(r"^\s*[\-\*\d\.\)]+\s+", "", ln).strip() for ln in text.splitlines()]
        qs = [ln for ln in lines if ln and ln.endswith("?")]
        return qs[:6] or [
            "Who are the primary users?",
            "Top 3 success criteria?",
            "Key constraints or integrations?",
            "Expected timeline?",
        ]
