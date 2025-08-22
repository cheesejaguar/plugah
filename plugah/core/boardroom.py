from __future__ import annotations

import asyncio
import os
from typing import Any, AsyncGenerator, Awaitable, Callable, Dict, List, Optional

from ..llm_client import LLMClient, LiteLLMClient
from ..adapters.base import ToolRegistry
from .discovery import DiscoveryEngine
from .events import EventBus
from .models import BudgetPolicy, Event, EventType, OrganizationGraph, PRD
from .planner import OrgPlanner
from .prd import PRDEngine
from .runner import LocalTaskRunner


class BoardRoom:
    """
    Slim MVP API for core phases. All methods are asyncio-friendly.
    """

    def __init__(
        self,
        llm: Optional[LLMClient] = None,
        registry: Optional[ToolRegistry] = None,
        default_budget_usd: Optional[float] = None,
        policy: Optional[BudgetPolicy] = None,
    ) -> None:
        self.llm = llm or LiteLLMClient()
        self.registry = registry or ToolRegistry.default()
        self.default_budget_usd = default_budget_usd or float(os.getenv("DEFAULT_BUDGET_USD", "100"))
        policy_env = os.getenv("BUDGET_POLICY", "balanced").lower()
        try:
            env_policy = BudgetPolicy(policy_env)
        except Exception:
            env_policy = BudgetPolicy.BALANCED
        self.policy = policy or env_policy
        self.bus = EventBus()

        # Phase state
        self._problem: Optional[str] = None
        self._questions: List[str] = []
        self._prd: Optional[PRD] = None
        self._org: Optional[OrganizationGraph] = None

    async def startup_phase(self, problem: str, budget_usd: float, policy: BudgetPolicy | str) -> List[str]:
        pol = BudgetPolicy(policy) if isinstance(policy, str) else policy
        self._problem = problem
        de = DiscoveryEngine(self.llm)
        qs = de.generate_questions(problem, pol.value)
        self._questions = qs
        await self.bus.publish(Event(type=EventType.PHASE_CHANGE, text="startup"))
        for q in qs:
            await self.bus.publish(Event(type=EventType.QUESTION, text=q))
        return qs

    async def process_discovery(self, answers: List[str], problem: str, budget_usd: float) -> PRD:
        pe = PRDEngine(self.llm)
        prd = pe.create(problem, answers)
        self._prd = prd
        await self.bus.publish(Event(type=EventType.PHASE_CHANGE, text="discovery", prd_id=prd.id))
        return prd

    async def plan_organization(self, prd: PRD, budget_usd: float, policy: BudgetPolicy | str) -> OrganizationGraph:
        pol = BudgetPolicy(policy) if isinstance(policy, str) else policy
        planner = OrgPlanner()
        org = planner.plan(prd.id, pol, self._problem or prd.title)
        self._org = org
        await self.bus.publish(Event(type=EventType.PLAN_CREATED, text="Organization planned", prd_id=prd.id))
        return org

    async def execute(self, on_event: Optional[Callable[[Event], Any]] = None) -> Dict[str, Any]:
        if not self._org:
            raise ValueError("No organization planned. Call plan_organization first.")
        runner = LocalTaskRunner(self.bus, self.registry)

        async def forward_events() -> None:
            async for ev in self.bus.subscribe():
                if on_event:
                    try:
                        on_event(ev)
                    except Exception:
                        pass

        # Start forwarder if callback supplied
        forward_task: Optional[asyncio.Task] = None
        if on_event:
            forward_task = asyncio.create_task(forward_events())

        try:
            res = await runner.run(self._org)
            return {"artifacts": res["artifacts"], "total_cost_estimate": res["cost"], "okr_snapshot": {}}
        finally:
            if forward_task:
                forward_task.cancel()

    # Convenience: async generator of serialized events (e.g., for SSE)
    async def event_stream(self) -> AsyncGenerator[str, None]:
        async for ev in self.bus.subscribe():
            yield ev.to_ndjson()
