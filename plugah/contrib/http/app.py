from __future__ import annotations

import os
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from ...core.boardroom import BoardRoom
from ...core.models import BudgetPolicy

app = FastAPI(title="Plugah Contrib HTTP", version="0.1")


class AppState:
    def __init__(self) -> None:
        self.br = BoardRoom()
        self._job_counter = 0

    def next_job(self) -> str:
        self._job_counter += 1
        return f"job-{self._job_counter}"


STATE = AppState()


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"ok": "true"}


@app.post("/start_project")
async def start_project(payload: dict[str, Any]) -> dict[str, Any]:
    problem = payload.get("problem") or ""
    if not problem:
        raise HTTPException(status_code=400, detail="problem is required")
    budget = float(payload.get("budget_usd") or os.getenv("DEFAULT_BUDGET_USD", 100))
    policy = payload.get("policy") or os.getenv("BUDGET_POLICY", "balanced")
    qs = await STATE.br.startup_phase(problem=problem, budget_usd=budget, policy=BudgetPolicy(policy))
    return {"questions": qs}


@app.post("/answer_discovery")
async def answer_discovery(payload: dict[str, Any]) -> dict[str, Any]:
    answers = payload.get("answers") or []
    problem = payload.get("problem") or "Project"
    budget = float(payload.get("budget_usd") or os.getenv("DEFAULT_BUDGET_USD", 100))
    prd = await STATE.br.process_discovery(answers=answers, problem=problem, budget_usd=budget)
    return {"prd_id": prd.id, "summary": prd.summary[:200]}


@app.post("/execute")
async def execute(payload: dict[str, Any], background: BackgroundTasks) -> dict[str, Any]:
    budget = float(payload.get("budget_usd") or os.getenv("DEFAULT_BUDGET_USD", 100))
    policy = payload.get("policy") or os.getenv("BUDGET_POLICY", "balanced")
    if not STATE.br._prd:
        raise HTTPException(status_code=400, detail="No PRD yet. Call answer_discovery first.")
    org = await STATE.br.plan_organization(STATE.br._prd, budget, BudgetPolicy(policy))

    job_id = STATE.next_job()

    async def _run() -> None:
        try:
            await STATE.br.execute()
        except Exception as e:  # Emit error event
            from ...core.models import Event, EventType

            await STATE.br.bus.publish(
                Event(type=EventType.ERROR, text=f"Execution error: {e}", prd_id=org.prd_id)
            )

    background.add_task(_run)
    return {"job_id": job_id}


@app.get("/events/stream")
async def events_stream() -> StreamingResponse:
    async def generator():
        async for line in STATE.br.event_stream():
            yield line

    return StreamingResponse(generator(), media_type="application/x-ndjson")
