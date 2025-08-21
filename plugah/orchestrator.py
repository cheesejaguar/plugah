"""
Stable public API for Plugah orchestrator
"""

import json
import os
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from .audit import AuditLogger
from .boardroom import Startup
from .budget import CFO, BudgetManager
from .executor import Executor
from .metrics import MetricsEngine
from .oag_schema import OAG, BudgetPolicy
from .patches import PatchManager
from .planner import Planner
from .selector import Selector
from .types import (
    PRD,
    Event,
    ExecutionResult,
    InvalidInput,
)


class BoardRoom:
    """
    Main orchestrator interface for Plugah

    Provides a stable API for the four-phase execution pipeline:
    1. startup_phase - Generate discovery questions
    2. process_discovery - Process answers to create PRD
    3. plan_organization - Create OAG from PRD
    4. execute - Execute the planned organization
    """

    def __init__(self, project_id: str | None = None):
        """Initialize BoardRoom orchestrator"""
        self.project_id = project_id or str(uuid.uuid4())
        self.audit_logger = AuditLogger(self.project_id)
        self.startup = Startup()
        self.planner: Planner | None = None
        self.executor: Executor | None = None
        self.oag: OAG | None = None
        self.prd: PRD | None = None
        self.budget_manager: BudgetManager | None = None
        self.cfo: CFO | None = None
        self.metrics_engine: MetricsEngine | None = None
        self.patch_manager: PatchManager | None = None
        self.events: list[Event] = []
        self.mock_mode = os.getenv("PLUGAH_MODE", "").lower() == "mock"
        self._state: dict[str, Any] = {}

    async def startup_phase(
        self,
        problem: str,
        budget_usd: float,
        model_hint: str | None = None,
        policy: BudgetPolicy | str = BudgetPolicy.BALANCED,
    ) -> list[str]:
        """
        Phase 1: Generate discovery questions based on the problem statement

        Args:
            problem: Problem statement or project description
            budget_usd: Total budget in USD
            model_hint: Optional model preference (e.g., "gpt-4")
            policy: Budget policy (CONSERVATIVE, BALANCED, or AGGRESSIVE)

        Returns:
            List of discovery questions
        """
        if not problem:
            raise InvalidInput("Problem statement is required", {"field": "problem"})

        if budget_usd <= 0:
            raise InvalidInput("Budget must be positive", {"field": "budget_usd", "value": budget_usd})

        # Convert string policy to enum if needed
        if isinstance(policy, str):
            try:
                policy = BudgetPolicy(policy.lower())
            except ValueError:
                raise InvalidInput(
                    f"Invalid budget policy: {policy}",
                    {"field": "policy", "valid_values": [p.value for p in BudgetPolicy]},
                ) from None

        self._state["problem"] = problem
        self._state["budget_usd"] = budget_usd
        self._state["model_hint"] = model_hint
        self._state["policy"] = policy.value

        if self.mock_mode:
            # Return mock questions for CI testing
            questions = [
                "Who are the primary users/customers for this solution?",
                "What are the top 3 success criteria that would define project completion?",
                "What technical constraints or requirements must be met?",
                "What is the expected timeline for delivery?",
                "Are there any existing systems or data sources to integrate with?",
            ]
        else:
            # Real implementation
            discovery = await self.startup.run(
                problem, budget_usd, {"model_hint": model_hint, "policy": policy.value}
            )
            questions = discovery.get("questions", [])

        self._state["questions"] = questions
        self._emit_event(
            Event(
                phase="startup",
                message=f"Generated {len(questions)} discovery questions",
                cost_delta=0.01 if not self.mock_mode else 0.0,
                acc_cost=0.01 if not self.mock_mode else 0.0,
            )
        )

        return questions

    async def process_discovery(
        self,
        answers: list[str],
        problem: str,
        budget_usd: float,
        model_hint: str | None = None,
        policy: BudgetPolicy | str = BudgetPolicy.BALANCED,
    ) -> PRD:
        """
        Phase 2: Process discovery answers to generate PRD

        Args:
            answers: Answers to discovery questions
            problem: Problem statement (must match startup_phase)
            budget_usd: Total budget (must match startup_phase)
            model_hint: Optional model preference
            policy: Budget policy

        Returns:
            Product Requirements Document (PRD)
        """
        if not answers:
            raise InvalidInput("Answers are required", {"field": "answers"})

        # Convert string policy to enum if needed
        if isinstance(policy, str):
            try:
                policy = BudgetPolicy(policy.lower())
            except ValueError:
                raise InvalidInput(f"Invalid budget policy: {policy}", {"field": "policy"}) from None

        self._state["answers"] = answers

        if self.mock_mode:
            # Return mock PRD for CI testing
            prd_data = {
                "title": "Mock Project",
                "problem_statement": problem,
                "budget": budget_usd,
                "domain": "general",
                "users": answers[0] if answers else "General users",
                "success_criteria": ["Criterion 1", "Criterion 2", "Criterion 3"],
                "constraints": ["Constraint 1", "Constraint 2"],
                "timeline": "ASAP",
                "integrations": "None",
                "objectives": [
                    {
                        "id": "obj_1",
                        "title": "Deliver Core Functionality",
                        "description": "Implement the core solution",
                    },
                    {
                        "id": "obj_2",
                        "title": "Ensure Quality",
                        "description": "Meet quality standards",
                    },
                ],
                "key_results": [
                    {
                        "id": "kr_1",
                        "objective_id": "obj_1",
                        "metric": "Feature Completion",
                        "target": 100,
                        "current": 0,
                        "unit": "%",
                    }
                ],
                "requirements": ["Requirement 1", "Requirement 2"],
                "milestones": [],
                "risks": ["Risk 1"],
                "non_goals": [],
                "created_at": "2024-01-01T00:00:00Z",
            }
        else:
            # Real implementation
            prd_data = await self.startup.process_answers(answers, problem, budget_usd)

        self.prd = PRD(prd_data)
        self._state["prd"] = prd_data

        self._emit_event(
            Event(
                phase="discovery",
                message="PRD generated successfully",
                cost_delta=0.02 if not self.mock_mode else 0.0,
                acc_cost=0.03 if not self.mock_mode else 0.0,
                metadata={"objectives": len(prd_data.get("objectives", []))},
            )
        )

        return self.prd

    async def plan_organization(
        self,
        prd: PRD,
        budget_usd: float,
        model_hint: str | None = None,
        policy: BudgetPolicy | str = BudgetPolicy.BALANCED,
    ) -> OAG:
        """
        Phase 3: Plan organizational structure from PRD

        Args:
            prd: Product Requirements Document
            budget_usd: Total budget
            model_hint: Optional model preference
            policy: Budget policy

        Returns:
            Organizational Agent Graph (OAG)
        """
        if not prd:
            raise InvalidInput("PRD is required", {"field": "prd"})

        # Convert string policy to enum if needed
        if isinstance(policy, str):
            try:
                policy = BudgetPolicy(policy.lower())
            except ValueError:
                raise InvalidInput(f"Invalid budget policy: {policy}", {"field": "policy"}) from None

        if self.mock_mode:
            # Create mock OAG for CI testing
            from .oag_schema import (
                AgentSpec,
                BudgetCaps,
                BudgetModel,
                Contract,
                CostTrack,
                OrgMeta,
                RoleLevel,
                TaskSpec,
                TaskStatus,
            )

            meta = OrgMeta(
                project_id=self.project_id,
                title=prd.to_dict().get("title", "Mock Project"),
                domain="general",
            )

            budget = BudgetModel(
                caps=BudgetCaps(hard_cap_usd=budget_usd, soft_cap_usd=budget_usd * 0.8),
                forecast_cost_usd=budget_usd * 0.5,
                policy=policy,
            )

            # Create minimal org structure
            ceo = AgentSpec(
                id="ceo",
                role="CEO",
                level=RoleLevel.C_SUITE,
                llm="gpt-3.5-turbo",
            )

            task = TaskSpec(
                id="task_1",
                description="Implement core functionality",
                agent_id="ceo",
                contract=Contract(definition_of_done="Task completed"),
                expected_output="Implementation complete",
                status=TaskStatus.PLANNED,
                cost=CostTrack(est_cost_usd=10.0),
            )

            self.oag = OAG(meta=meta, budget=budget, nodes={"ceo": ceo, "task_1": task})
        else:
            # Real implementation
            selector = Selector(budget_policy=policy.value)
            self.planner = Planner(selector)
            self.oag = self.planner.plan(prd.to_dict(), budget_usd)

        # Initialize supporting components
        self.budget_manager = BudgetManager(self.oag.budget)
        self.cfo = CFO(self.budget_manager)
        self.metrics_engine = MetricsEngine(self.oag)
        self.patch_manager = PatchManager(self.oag, self.audit_logger)

        self._state["oag"] = self.oag.model_dump()

        self._emit_event(
            Event(
                phase="planning",
                message=f"Created org with {len(self.oag.get_agents())} agents and {len(self.oag.get_tasks())} tasks",
                cost_delta=0.05 if not self.mock_mode else 0.0,
                acc_cost=0.08 if not self.mock_mode else 0.0,
                metadata={
                    "agents": len(self.oag.get_agents()),
                    "tasks": len(self.oag.get_tasks()),
                },
            )
        )

        return self.oag

    async def execute(
        self, oag: OAG | None = None, *, on_event: Any | None = None
    ) -> ExecutionResult:
        """
        Phase 4: Execute the planned organization

        Args:
            oag: Optional OAG to execute (uses internal OAG if not provided)
            on_event: Optional callback for execution events

        Returns:
            ExecutionResult with total_cost, artifacts, metrics, and details
        """
        if oag:
            self.oag = oag
            # Reinitialize components for new OAG
            self.budget_manager = BudgetManager(self.oag.budget)
            self.cfo = CFO(self.budget_manager)
            self.metrics_engine = MetricsEngine(self.oag)
            self.patch_manager = PatchManager(self.oag, self.audit_logger)

        if not self.oag:
            raise InvalidInput("No OAG to execute. Run plan_organization first or provide an OAG")

        if self.mock_mode:
            # Mock execution for CI testing
            total_cost = 0.1
            artifacts = {"output": "Mock execution complete"}
            metrics = {"completion_rate": 100, "tasks_completed": len(self.oag.get_tasks())}
            details = {
                "project_id": self.project_id,
                "tasks": len(self.oag.get_tasks()),
                "agents": len(self.oag.get_agents()),
            }
        else:
            # Real execution
            self.executor = Executor(self.oag, self.budget_manager)

            # Add event callback if provided
            if on_event:
                self.executor.add_callback(on_event)

            # Execute
            results = await self.executor.execute(parallel=True)

            # Calculate final metrics
            final_metrics = self.metrics_engine.calculate_all()

            total_cost = self.budget_manager.get_spent()
            artifacts = {}
            for result in results.values():
                if hasattr(result, "output") and isinstance(result.output, dict):
                    artifacts.update(result.output.get("artifacts", {}))

            metrics = final_metrics
            details = {
                "project_id": self.project_id,
                "results": len(results),
                "budget_remaining": self.budget_manager.get_remaining(),
            }

        self._emit_event(
            Event(
                phase="execution",
                message="Execution complete",
                cost_delta=total_cost,
                acc_cost=total_cost,
                metadata={"total_cost": total_cost},
            )
        )

        return ExecutionResult(
            total_cost=total_cost, artifacts=artifacts, metrics=metrics, details=details
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Export current state to dictionary for persistence

        Returns:
            Dictionary containing all state
        """
        state = {
            "project_id": self.project_id,
            "state": self._state.copy(),
            "events": [e.to_dict() for e in self.events],
        }

        if self.prd:
            state["prd"] = self.prd.to_dict()

        if self.oag:
            state["oag"] = self.oag.model_dump()

        if self.budget_manager:
            state["budget"] = {
                "spent": self.budget_manager.get_spent(),
                "remaining": self.budget_manager.get_remaining(),
                "alerts": self.budget_manager.alerts,
            }

        return state

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BoardRoom":
        """
        Create BoardRoom instance from saved state

        Args:
            data: State dictionary from to_dict()

        Returns:
            Restored BoardRoom instance
        """
        br = cls(project_id=data.get("project_id"))
        br._state = data.get("state", {})

        if "prd" in data:
            br.prd = PRD(data["prd"])

        if "oag" in data:
            from .oag_schema import OAG as OAGSchema  # noqa: N811

            br.oag = OAGSchema.model_validate(data["oag"])
            br.budget_manager = BudgetManager(br.oag.budget)
            br.cfo = CFO(br.budget_manager)
            br.metrics_engine = MetricsEngine(br.oag)
            br.patch_manager = PatchManager(br.oag, br.audit_logger)

        if "budget" in data and br.budget_manager:
            br.budget_manager.spent = data["budget"].get("spent", 0)
            br.budget_manager.alerts = data["budget"].get("alerts", [])

        return br

    def save_state(self, path: Path | str) -> None:
        """
        Save state to file

        Args:
            path: File path to save state
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    def load_state(self, path: Path | str) -> None:
        """
        Load state from file

        Args:
            path: File path to load state from
        """
        path = Path(path)

        with open(path) as f:
            data = json.load(f)

        # Update current instance
        self._state = data.get("state", {})

        if "prd" in data:
            self.prd = PRD(data["prd"])

        if "oag" in data:
            from .oag_schema import OAG as OAGSchema  # noqa: N811

            self.oag = OAGSchema.model_validate(data["oag"])
            self.budget_manager = BudgetManager(self.oag.budget)
            self.cfo = CFO(self.budget_manager)
            self.metrics_engine = MetricsEngine(self.oag)
            self.patch_manager = PatchManager(self.oag, self.audit_logger)

    async def events_stream(self) -> AsyncIterator[Event]:
        """
        Async iterator for events (for streaming)

        Yields:
            Event objects as execution progresses
        """
        for event in self.events:
            yield event

        # In real implementation, this would yield events as they occur
        # For now, just return historical events

    def _emit_event(self, event: Event) -> None:
        """Internal method to emit and store events"""
        self.events.append(event)

        # Log to audit
        self.audit_logger.log_event(
            event.phase,
            {
                "message": event.message,
                "cost_delta": event.cost_delta,
                "acc_cost": event.acc_cost,
                "metadata": event.metadata,
            },
        )
