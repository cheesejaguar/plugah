from __future__ import annotations

import asyncio
from typing import Any

from ..adapters.base import ToolRegistry
from .events import EventBus
from .models import Event, EventType, OrganizationGraph


class LocalTaskRunner:
    def __init__(self, bus: EventBus, registry: ToolRegistry | None = None) -> None:
        self.bus = bus
        self.registry = registry or ToolRegistry.default()
        self._spent = 0.0

    @property
    def spent(self) -> float:
        return self._spent

    async def _emit(self, event: Event) -> None:
        await self.bus.publish(event)

    async def run(self, org: OrganizationGraph) -> dict[str, Any]:
        await self._emit(Event(type=EventType.PHASE_CHANGE, text="Execution started", prd_id=org.prd_id))
        # Hire events (simulated)
        for role in org.c_suite + org.ics:
            await self._emit(Event(type=EventType.HIRE, text=f"Hired {role.name}", role=role.name, prd_id=org.prd_id))

        # Execute tasklets sequentially for determinism
        artifacts: dict[str, Any] = {}
        for t in org.tasklets:
            await self._emit(
                Event(type=EventType.TASK_STARTED, text=f"Task {t.title} started", task_id=t.id, role=t.role, prd_id=org.prd_id)
            )
            # Route to tools when obvious
            if "issue" in t.title.lower() or "github" in t.title.lower():
                gh = self.registry.get("github_issues")
                if gh:
                    res = gh.run({
                        "action": "create_issue",
                        "title": t.title,
                        "body": f"Auto-created for {t.role}",
                    })
                    artifacts[f"github:{t.id}"] = res
                    self._spent += 0.01
            elif "doc" in t.title.lower() or "summary" in t.title.lower():
                gd = self.registry.get("gdrive_docs")
                if gd:
                    res = gd.run({
                        "action": "create_doc",
                        "title": t.title,
                        "markdown_body": f"# {t.title}\nSeed document",
                    })
                    artifacts[f"gdrive:{t.id}"] = res
                    self._spent += 0.01
            else:
                # Simulated compute
                await asyncio.sleep(0)
                artifacts[t.id] = {"note": "simulated"}

            await self._emit(
                Event(type=EventType.TASK_DONE, text=f"Task {t.title} done", task_id=t.id, role=t.role, prd_id=org.prd_id)
            )

        await self._emit(Event(type=EventType.FINISHED, text="Execution finished", prd_id=org.prd_id))
        return {"artifacts": artifacts, "cost": self._spent}
