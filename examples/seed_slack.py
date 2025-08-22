"""
Seeded end-to-end run for the Slack summarizer demo. Uses DRY_RUN by default.
Run with: python -m examples.seed_slack
"""

import asyncio
import os
import sys
from pathlib import Path

# Ensure repo root on path when executed as a module or script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from plugah.core.boardroom import BoardRoom
from plugah.core.models import BudgetPolicy, Event


async def main() -> None:
    os.environ.setdefault("DRY_RUN", "true")
    br = BoardRoom()

    problem = "Spin up a project to ship a Slack summarizer"
    questions = await br.startup_phase(problem=problem, budget_usd=100, policy=BudgetPolicy.BALANCED)
    print("Questions:")
    for q in questions:
        print("-", q)

    answers = [
        "PMs and Eng leads",
        "Daily across #eng-updates and #incidents",
        "Respect confidential channels",
        "Post to #summaries and store in Drive",
        "Daily summaries",
        "Leads and managers",
    ]
    prd = await br.process_discovery(answers=answers, problem=problem, budget_usd=100)
    org = await br.plan_organization(prd=prd, budget_usd=100, policy=BudgetPolicy.BALANCED)

    print("\nStreaming events:")

    async def consume():
        async for line in br.event_stream():
            print(line.strip())

    consumer = asyncio.create_task(consume())
    await br.execute()
    await asyncio.sleep(0.1)
    consumer.cancel()


if __name__ == "__main__":
    asyncio.run(main())
