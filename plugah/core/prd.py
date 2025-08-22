from __future__ import annotations

import re
import uuid
from typing import Dict, List, Optional

from ..llm_client import LLMClient, LiteLLMClient
from .models import PRD


SLACK_RE = re.compile(r"slack\s+summarizer", re.I)


class PRDEngine:
    def __init__(self, llm: Optional[LLMClient] = None) -> None:
        self.llm = llm or LiteLLMClient()

    def create(self, problem: str, answers: List[str]) -> PRD:
        prd_id = str(uuid.uuid4())

        # Slack seeded plan
        if SLACK_RE.search(problem or ""):
            initial_workplan = [
                "M1: Connect Slack API + channel scope",
                "M2: Summarization prompts + privacy filter",
                "M3: Deliver summaries to target channel and Drive",
            ]
        else:
            initial_workplan = ["M1: Discovery", "M2: Prototype", "M3: Deliverable"]

        system = (
            "Create a concise PRD. Fields: objective, users, scope (list), "
            "success_metrics (list), risks (list), constraints (list)."
        )
        user = f"Problem: {problem}. Answers: {answers}"
        text = self.llm.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
        )

        # Simple parsing fallback; do not rely on LLM structure
        title = (problem or "Project").strip()[:64]
        summary = text.strip() if text else f"PRD for {title}"
        acceptance = ["Defined milestones", "Measurable summaries", "Privacy respected"]
        risks = ["Ambiguous scope", "API limits"]

        return PRD(
            id=prd_id,
            title=title,
            summary=summary,
            acceptance_criteria=acceptance,
            risks=risks,
            objective="Ship an initial usable solution",
            users=answers[0] if answers else "General users",
            scope=["MVP only"],
            success_metrics=["On-time", "Usable", "Low cost"],
            constraints=["Keep it simple"],
            initial_workplan=initial_workplan,
        )
