# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Development Setup
```bash
# Use uv for Python package management (REQUIRED)
uv venv
source .venv/bin/activate  # On Unix/macOS
uv pip install -e ".[dev,demo]"
```

### Running the Application
```bash
# CLI Demo
python -m plugah.demo.demo_cli --prompt "Your project description" --budget 100

# Web Interface (run in separate terminals)
# Backend:
uvicorn web.backend.main:app --reload

# Frontend:
cd web/frontend
npm install  # First time only
npm run dev
```

### Testing and Quality
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_planner.py

# Run with coverage
pytest --cov=plugah --cov-report=term-missing

# Type checking
mypy plugah

# Linting
ruff check plugah

# Format code
black plugah
```

## Architecture Overview

### Core Flow: Startup → Planning → Execution

1. **Startup Discovery Phase** (`boardroom.py:Startup`)
   - Co-founders (CEO/CTO) generate questions about the project
   - Answers are processed into a PRD (Product Requirements Document)
   - PRD contains objectives, constraints, success criteria, OKRs, and KPIs

2. **Planning Phase** (`planner.py:Planner`)
   - Takes PRD + budget → generates OAG (Organizational Agent Graph)
   - Creates hierarchy: Board Room (CEO/CTO/CFO) → VPs → Directors → Managers → ICs
   - Assigns tasks with explicit contracts (inputs/outputs/DoD)
   - Selects budget policy (conservative/balanced/aggressive) based on scope

3. **Execution Phase** (`executor.py:Executor`)
   - Materializes OAG into CrewAI agents (`materialize.py`)
   - Executes tasks in DAG order with budget gates
   - CFO monitors spending and triggers downgrades at soft cap thresholds
   - Emits events for real-time monitoring

### Key Data Structure: OAG (Organizational Agent Graph)

The OAG (`oag_schema.py`) is the central data structure representing the virtual company:
- **Nodes**: `AgentSpec` (employees) and `TaskSpec` (work items)
- **Edges**: Dependencies and reporting relationships with I/O mappings
- **Contracts**: Every task has explicit input/output specifications
- **Budget Model**: Soft cap (warning threshold) and hard cap (absolute limit)

### Budget Control System

The CFO (`budget.py:CFO`) enforces a two-tier budget system:
- **Soft Cap (80% of budget)**: Triggers warnings and model downgrades
- **Hard Cap (100% of budget)**: Absolute spending limit
- Alert levels: NORMAL → WARNING (70%) → CRITICAL (90%) → EXCEEDED_SOFT → EMERGENCY

When approaching limits, the system automatically:
1. Downgrades LLM models (premium → standard → economy)
2. Reduces tool availability
3. Can trigger JSON patches to modify the plan

### Dynamic Adjustments via JSON-Patch

The system uses RFC6902 JSON patches (`patches.py`) to modify the OAG during execution:
- Budget policy changes
- Model downgrades
- Task status updates
- Team size adjustments

All patches are logged for audit trail.

### Web API Structure

Backend (`web/backend/`):
- `routes_startup.py`: Discovery phase endpoints
- `routes_run.py`: Planning and execution with SSE streaming
- `routes_status.py`: Current state queries
- Sessions stored in memory (use Redis in production)

Frontend (`web/frontend/src/`):
- React + TypeScript + Tailwind CSS
- Components mirror the execution phases
- Real-time updates via Server-Sent Events (SSE)

### Tool System

Tools are registered in `registry.py` with:
- Category and tags for selection
- Cost tiers (1=cheap, 2=moderate, 3=expensive)
- Role preferences (e.g., VP Eng prefers code_reader)

Tool stubs in `tools/` implement CrewAI's BaseTool interface.

## Important Implementation Details

### Selector Logic (`selector.py`)
- Determines staffing levels based on budget and scope
- Assigns specializations (e.g., "Frontend Engineer" for web domain)
- Selects appropriate LLM models based on role level and budget policy
- Tool selection considers role preferences and budget constraints

### Metrics System (`metrics.py`)
- OKRs cascade from C-suite down the hierarchy
- KPIs roll up from ICs to managers to directors
- Health scores computed from task completion, budget usage, and metric attainment
- Subtree aggregation for organizational rollups

### Audit System (`audit.py`)
- Creates `.runs/{project_id}/` directory for each execution
- Logs all events to `logs/events.jsonl`
- Saves artifacts, patches, and metrics snapshots
- Generates summary reports

## Testing Strategy

Tests focus on contract validation and budget enforcement:
- `test_planner.py`: Ensures Board Room creation and task generation
- `test_oag_contracts.py`: Validates I/O contract consistency
- `test_budget.py`: Tests CFO enforcement and alert thresholds

Mock LLM responses for deterministic testing.

## Known Limitations

- Sessions are stored in memory (not production-ready)
- Tool implementations are stubs
- CrewAI execution is mocked in tests
- No authentication/authorization implemented
- Frontend SSE reconnection not implemented