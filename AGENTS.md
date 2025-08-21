# Repository Guidelines

## Project Structure & Module Organization
- `plugah/`: Core Python package (orchestrator `BoardRoom`, OAG schema, planner, executor, tools).
- `web/backend/`: FastAPI API (`main.py`, startup/run/status routes).
- `web/frontend/`: Vite + React + Tailwind UI (`src/`, `index.html`).
- `tests/`: Pytest suite (`test_*.py`).
- `.github/workflows/`: CI pipelines (lint, tests, build, integration).

## Build, Test, and Development Commands
- Install (dev/demo): `uv pip install -e ".[dev,demo]"`
- Run tests (45% gate): `pytest` or `pytest --cov=plugah --cov-report=term-missing`
- Lint/format (Ruff): `ruff format plugah tests && ruff check plugah tests && ruff format --check plugah tests`
- Type check: `mypy plugah`
- CLI demo: `plugah-demo --prompt "Test" --budget 100`
- Backend: `uvicorn web.backend.main:app --reload`
- Frontend: `cd web/frontend && npm ci || npm install && npm run dev`

## Coding Style & Naming Conventions
- Python: PEP 8, 100-char lines, type hints required; modules/functions `snake_case`, classes `PascalCase`.
- Tools: Ruff (format + lint), Mypy (strict). Pre-commit runs Ruff in CI order.
- TypeScript/React: Functional components + hooks, Tailwind utilities; keep files scoped by feature.

## Testing Guidelines
- Framework: Pytest; files `tests/test_*.py`.
- Coverage: Minimum 45% (CI enforced). Improve when possible.
- Patterns: Mock external calls; for deterministic runs set `PLUGAH_MODE=mock`.
- Async: Use `@pytest.mark.asyncio` for async tests.

## Commit & Pull Request Guidelines
- Conventional Commits (e.g., `feat: add planner rule`, `fix: budget cap rounding`).
- PRs: Use the template; include description, linked issues, tests, and pass lint/type checks.
- Keep diffs focused; update docs (README/CONTRIBUTING/CHANGELOG) when relevant.

## Security & Configuration Tips
- LLM config: set `OPENAI_API_KEY`; model defaults to `gpt-5-nano` (override with `OPENAI_MODEL` or `DEFAULT_LLM_MODEL`).
- Execution modes: `PLUGAH_MODE=mock` for CI/testing; `PLUGAH_REAL_EXECUTION=1` to enable CrewAI task execution.
- See `SECURITY.md` for vulnerability reporting.

