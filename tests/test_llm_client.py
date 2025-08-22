
import pytest

from plugah.core.boardroom import BoardRoom
from plugah.core.models import BudgetPolicy
from plugah.llm_client import LLMClient


class FakeLLM(LLMClient):
    def chat(self, messages: list[dict[str, str]], model=None, temperature=None) -> str:  # type: ignore[override]
        # Return a deterministic tiny summary
        return "objective: deliver mvp; users: pm; scope: mvp; metrics: simple"


@pytest.mark.asyncio
async def test_discovery_and_prd_with_fake_llm():
    br = BoardRoom(llm=FakeLLM())
    qs = await br.startup_phase("Slack summarizer", 100, BudgetPolicy.BALANCED)
    assert 3 <= len(qs) <= 6
    prd = await br.process_discovery(["PMs"], problem="Slack summarizer", budget_usd=100)
    assert prd.title.lower().startswith("slack") or prd.title
    assert prd.initial_workplan, "should include seeded workplan"
