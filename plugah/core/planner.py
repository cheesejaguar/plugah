from __future__ import annotations

from .models import BudgetPolicy, OrganizationGraph, Role, Tasklet


class OrgPlanner:
    def plan(self, prd_id: str, policy: BudgetPolicy, problem: str) -> OrganizationGraph:
        # Base C-suite
        c_suite = [
            Role(name="CEO", goals=["Deliver MVP"], inputs=["PRD"], outputs=["Direction"]),
            Role(name="CTO", goals=["Technical plan"], inputs=["PRD"], outputs=["Spec"]),
            Role(name="CFO", goals=["Track cost"], inputs=["Plan"], outputs=["Budget report"]),
        ]

        ics: list[Role] = []
        tasklets: list[Tasklet] = []

        # Policy hint: fewer ICs if CHEAP, more if FAST
        ic_count = 3
        if policy == BudgetPolicy.CHEAP:
            ic_count = 2
        elif policy == BudgetPolicy.FAST:
            ic_count = 4

        # Slack seed: leaner org
        if "slack" in problem.lower() and "summarizer" in problem.lower():
            c_suite = [Role(name="CEO"), Role(name="VP Eng"), Role(name="CFO")]
            ics = [Role(name="IC Summarizer"), Role(name="IC Integrations")]
            tasklets = [
                Tasklet(id="task-1", title="Summarize channels", role="IC Summarizer"),
                Tasklet(id="task-2", title="Ship delivery hook", role="IC Integrations"),
            ]
        else:
            for i in range(ic_count):
                ics.append(Role(name=f"IC-{i+1}", goals=["Ship task"], outputs=["Artifact"]))
                tasklets.append(Tasklet(id=f"task-{i+1}", title=f"Task {i+1}", role=f"IC-{i+1}"))

        return OrganizationGraph(prd_id=prd_id, c_suite=c_suite, ics=ics, tasklets=tasklets)

