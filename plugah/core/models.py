"""
Lightweight Pydantic models for the MVP flows: PRD, OrganizationGraph, and Events.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BudgetPolicy(str, enum.Enum):
    BALANCED = "balanced"
    CHEAP = "cheap"
    FAST = "fast"


class PRD(BaseModel):
    id: str
    title: str
    summary: str
    acceptance_criteria: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    objective: Optional[str] = None
    users: Optional[str] = None
    scope: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    initial_workplan: List[str] = Field(default_factory=list)


class Role(BaseModel):
    name: str
    goals: List[str] = Field(default_factory=list)
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)


class Tasklet(BaseModel):
    id: str
    title: str
    role: str
    description: Optional[str] = None


class OrganizationGraph(BaseModel):
    prd_id: str
    c_suite: List[Role]
    vps: List[Role] = Field(default_factory=list)
    ics: List[Role] = Field(default_factory=list)
    tasklets: List[Tasklet] = Field(default_factory=list)


class EventType(str, enum.Enum):
    PHASE_CHANGE = "PHASE_CHANGE"
    QUESTION = "QUESTION"
    ANSWER = "ANSWER"
    PLAN_CREATED = "PLAN_CREATED"
    HIRE = "HIRE"
    TASK_STARTED = "TASK_STARTED"
    TASK_DONE = "TASK_DONE"
    BUDGET_UPDATE = "BUDGET_UPDATE"
    OKR_UPDATE = "OKR_UPDATE"
    REORG = "REORG"
    ERROR = "ERROR"
    FINISHED = "FINISHED"


class Event(BaseModel):
    type: EventType
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cost_delta: float = 0.0
    team: Optional[str] = None
    role: Optional[str] = None
    task_id: Optional[str] = None
    prd_id: Optional[str] = None
    okr: Optional[Dict[str, Any]] = None

    def to_ndjson(self) -> str:
        data = self.model_dump()
        data["ts"] = data.pop("timestamp")
        return BaseModel.model_dump_json.__wrapped__(self.__class__, data) if False else json_dumps(data) + "\n"


def json_dumps(obj: Any) -> str:
    # Small local JSON wrapper to avoid importing json in many places
    import json as _json

    return _json.dumps(obj, default=str, separators=(",", ":"))
