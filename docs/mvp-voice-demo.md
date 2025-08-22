# Plugah MVP — Pipecat Flows + LiteLLM

This MVP exposes a slim, reliable pipeline that pairs with a Pipecat Flows voice UI and a LiteLLM router.

Flow (voice gateway speaks in italics):
- start_project → discovery questions (Pipecat: “I have a few questions…”) 
- answer_discovery → PRD summary (Pipecat: “Drafted the plan…”) 
- execute → plan + run + stream events (Pipecat narrates PHASE_CHANGE, HIRE, TASK_*)

Components:
- LLM: `LiteLLMClient` (OpenAI-compatible HTTP; no provider SDK).
- Engines: `DiscoveryEngine`, `PRDEngine`, `OrgPlanner`, `LocalTaskRunner`.
- Events: `EventBus` + `Event` (newline-delimited JSON for SSE).
- Tools: `GitHubIssuesAdapter`, `GDriveDocsAdapter` (both dry-run aware).
- HTTP: `plugah.contrib.http` FastAPI app (`/start_project`, `/answer_discovery`, `/execute`, `/events/stream`).

See `examples/slack_summarizer_quickstart.md` for curl and Python usage.
