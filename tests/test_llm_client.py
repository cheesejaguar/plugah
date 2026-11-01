import json

import httpx
import pytest

from plugah.core.boardroom import BoardRoom
from plugah.core.models import BudgetPolicy
from plugah.llm_client import LiteLLMClient, LLMClient

FAKE_SUMMARY = "objective: deliver mvp; users: pm; scope: mvp; metrics: simple"


class FakeLLM(LLMClient):
    """Stands in for the external LLM provider; records the prompts it receives."""

    def __init__(self) -> None:
        self.calls: list[list[dict[str, str]]] = []

    def chat(self, messages: list[dict[str, str]], model=None, temperature=None) -> str:  # type: ignore[override]
        self.calls.append(messages)
        return FAKE_SUMMARY


@pytest.mark.asyncio
async def test_discovery_and_prd_with_fake_llm():
    llm = FakeLLM()
    br = BoardRoom(llm=llm)
    qs = await br.startup_phase("Slack summarizer", 100, BudgetPolicy.BALANCED)
    # Slack summarizer problems use seeded questions without calling the LLM
    assert len(qs) == 6
    assert qs[0] == "Which workspace and channels are in scope?"
    assert llm.calls == []

    prd = await br.process_discovery(["PMs"], problem="Slack summarizer", budget_usd=100)
    assert prd.title == "Slack summarizer"
    assert prd.summary == FAKE_SUMMARY
    assert prd.users == "PMs"
    assert prd.initial_workplan[0] == "M1: Connect Slack API + channel scope"
    # The PRD prompt carries the problem and the discovery answers
    assert len(llm.calls) == 1
    user_msg = llm.calls[0][-1]
    assert user_msg["role"] == "user"
    assert "Slack summarizer" in user_msg["content"]
    assert "PMs" in user_msg["content"]


@pytest.mark.asyncio
async def test_discovery_parses_llm_questions():
    class ListLLM(FakeLLM):
        def chat(self, messages, model=None, temperature=None):  # type: ignore[override]
            self.calls.append(messages)
            return "1. Who uses it?\n- What is the deadline?\nNot a question\n* Budget limits?"

    br = BoardRoom(llm=ListLLM())
    qs = await br.startup_phase("Inventory tracker", 100, BudgetPolicy.BALANCED)
    assert qs == ["Who uses it?", "What is the deadline?", "Budget limits?"]


def _client_with(handler) -> LiteLLMClient:
    return LiteLLMClient(
        base_url="http://litellm.local/",
        api_key="test-key",
        default_model="route.default",
        extra_headers_json='{"X-Team": "plugah"}',
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_litellm_client_builds_request_and_parses_response():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["headers"] = request.headers
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "  hello  "}}]})

    client = _client_with(handler)
    out = client.chat([{"role": "user", "content": "hi"}], temperature=0.2)

    assert out == "hello"
    assert seen["url"] == "http://litellm.local/v1/chat/completions"
    assert seen["headers"]["authorization"] == "Bearer test-key"
    assert seen["headers"]["x-team"] == "plugah"
    assert seen["body"] == {
        "model": "route.default",
        "messages": [{"role": "user", "content": "hi"}],
        "temperature": 0.2,
    }


def test_litellm_client_omits_temperature_and_honors_model_override():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    client = _client_with(handler)
    client.chat([{"role": "user", "content": "hi"}], model="gpt-x")
    assert seen["body"] == {"model": "gpt-x", "messages": [{"role": "user", "content": "hi"}]}


def test_litellm_client_falls_back_to_user_text_on_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    client = _client_with(handler)
    out = client.chat(
        [{"role": "system", "content": "sys"}, {"role": "user", "content": "the question"}]
    )
    assert out == "the question"


def test_litellm_client_without_base_url_echoes_user_content(monkeypatch):
    monkeypatch.delenv("LITELLM_BASE_URL", raising=False)

    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - must not be hit
        raise AssertionError("no HTTP call expected without a base URL")

    client = LiteLLMClient(client=httpx.Client(transport=httpx.MockTransport(handler)))
    out = client.chat(
        [
            {"role": "system", "content": "ignored"},
            {"role": "user", "content": "a"},
            {"role": "user", "content": "b"},
        ]
    )
    assert out == "a\nb"


def test_litellm_client_ignores_malformed_extra_headers(monkeypatch):
    monkeypatch.delenv("LITELLM_API_KEY", raising=False)
    client = LiteLLMClient(base_url="http://x", extra_headers_json="not json")
    assert client._headers == {"Content-Type": "application/json"}
