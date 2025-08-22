# Slack Summarizer Quickstart (MVP)

Prereqs: Python 3.10+, optional LiteLLM router. For dry-run, only env is `DRY_RUN=true`.

- Pure API (Python):
  1. `export DRY_RUN=true` (and optionally set `LITELLM_BASE_URL` if available)
  2. `python examples/seed_slack.py`
  3. Observe discovery, PRD, plan, and NDJSON event stream in console.

- HTTP SSE service (optional extra `http`):
  1. `uv pip install -e ".[dev]"` and `uv pip install fastapi uvicorn`
  2. `uvicorn plugah.contrib.http.app:app --reload`
  3. `curl -N localhost:8000/healthz`
  4. `curl -s localhost:8000/start_project -H 'content-type: application/json' -d '{"problem":"Spin up a project to ship a Slack summarizer","budget_usd":100,"policy":"balanced"}'`
  5. `curl -s localhost:8000/answer_discovery -H 'content-type: application/json' -d '{"answers":["PMs"],"problem":"Slack summarizer","budget_usd":100}'`
  6. `curl -s localhost:8000/execute -H 'content-type: application/json' -d '{"budget_usd":100,"policy":"balanced"}'`
  7. `curl -N localhost:8000/events/stream` to stream NDJSON events.
