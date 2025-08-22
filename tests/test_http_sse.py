import json

import pytest


def _fastapi_available() -> bool:
    try:
        import fastapi  # noqa: F401

        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _fastapi_available(), reason="http extra not installed")


@pytest.mark.asyncio
async def test_http_sse_smoke():
    from fastapi.testclient import TestClient

    from plugah.contrib.http.app import app

    client = TestClient(app)

    # Start project
    r = client.post(
        "/start_project",
        json={"problem": "Spin up a project to ship a Slack summarizer", "budget_usd": 100, "policy": "balanced"},
    )
    assert r.status_code == 200
    qs = r.json()["questions"]
    assert len(qs) >= 3

    # Answer discovery
    r = client.post(
        "/answer_discovery",
        json={"answers": ["PMs"], "problem": "Slack summarizer", "budget_usd": 100},
    )
    assert r.status_code == 200
    prd_id = r.json()["prd_id"]
    assert prd_id

    # Execute
    r = client.post(
        "/execute",
        json={"budget_usd": 100, "policy": "balanced"},
    )
    assert r.status_code == 200
    job_id = r.json()["job_id"]
    assert job_id

    # Stream events (just read a few lines)
    with client.stream("GET", "/events/stream") as s:
        lines = []
        for line in s.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            lines.append(data["type"])  # type: ignore[index]
            if len(lines) >= 3:
                break
    assert any(t in {"PHASE_CHANGE", "PLAN_CREATED", "TASK_STARTED", "TASK_DONE"} for t in lines)

