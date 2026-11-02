import asyncio
import json

import pytest


def _fastapi_available() -> bool:
    try:
        import fastapi  # noqa: F401

        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _fastapi_available(), reason="http extra not installed")


@pytest.fixture
def http_app(monkeypatch):
    # No LiteLLM endpoint: LiteLLMClient falls back to echoing the user prompt
    monkeypatch.delenv("LITELLM_BASE_URL", raising=False)
    monkeypatch.delenv("DRY_RUN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    from plugah.contrib.http import app as app_module

    # Fresh per-test state so tests don't leak into each other
    monkeypatch.setattr(app_module, "STATE", app_module.AppState())
    return app_module


def test_http_phases_end_to_end(http_app):
    from fastapi.testclient import TestClient

    client = TestClient(http_app.app)

    assert client.get("/healthz").json() == {"ok": "true"}

    # Start project: the Slack summarizer problem uses seeded questions
    r = client.post(
        "/start_project",
        json={
            "problem": "Spin up a project to ship a Slack summarizer",
            "budget_usd": 100,
            "policy": "balanced",
        },
    )
    assert r.status_code == 200
    qs = r.json()["questions"]
    assert len(qs) == 6
    assert qs[0] == "Which workspace and channels are in scope?"

    # Answer discovery
    r = client.post(
        "/answer_discovery",
        json={"answers": ["PMs"], "problem": "Slack summarizer", "budget_usd": 100},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["prd_id"] == http_app.STATE.br._prd.id
    assert "PMs" in body["summary"]

    # Execute (TestClient runs the background task before returning)
    r = client.post("/execute", json={"budget_usd": 100, "policy": "balanced"})
    assert r.status_code == 200
    assert r.json() == {"job_id": "job-1"}
    assert http_app.STATE.br._org is not None
    assert http_app.STATE.br._org.prd_id == body["prd_id"]


def test_http_validation_errors(http_app):
    from fastapi.testclient import TestClient

    client = TestClient(http_app.app)

    r = client.post("/start_project", json={"problem": ""})
    assert r.status_code == 400
    assert r.json()["detail"] == "problem is required"

    r = client.post("/execute", json={"budget_usd": 100})
    assert r.status_code == 400
    assert "answer_discovery" in r.json()["detail"]


@pytest.mark.asyncio
async def test_events_stream_emits_ndjson(http_app):
    br = http_app.STATE.br
    response = await http_app.events_stream()
    assert response.media_type == "application/x-ndjson"

    lines: list[dict] = []

    async def read_three():
        async for chunk in response.body_iterator:
            text = chunk.decode() if isinstance(chunk, bytes) else chunk
            lines.append(json.loads(text))
            if len(lines) >= 3:
                break

    reader = asyncio.create_task(read_three())
    for _ in range(100):
        if br.bus._subscribers:
            break
        await asyncio.sleep(0)
    assert br.bus._subscribers, "stream never subscribed to the event bus"

    await br.startup_phase("Slack summarizer", 100, "balanced")
    await asyncio.wait_for(reader, timeout=5)

    assert [ln["type"] for ln in lines] == ["PHASE_CHANGE", "QUESTION", "QUESTION"]
    assert lines[0]["text"] == "startup"
    assert lines[1]["text"] == "Which workspace and channels are in scope?"
