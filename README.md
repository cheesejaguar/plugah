# Plugah.ai 🧠

![CI](https://github.com/cheesejaguar/plugah/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/cheesejaguar/plugah/branch/main/graph/badge.svg)](https://codecov.io/gh/cheesejaguar/plugah)
[![PyPI version](https://img.shields.io/pypi/v/plugah.svg)](https://pypi.org/project/plugah/)
[![Python versions](https://img.shields.io/pypi/pyversions/plugah.svg)](https://pypi.org/project/plugah/)
[![License: MIT](https://img.shields.io/github/license/cheesejaguar/plugah.svg)](LICENSE)

Multi-agent orchestration system with organizational hierarchy - dynamically generates and manages AI agent organizations to deliver projects within budget constraints.

## Overview

Plugah.ai creates a virtual organization of AI agents to tackle complex projects. While the system uses a business hierarchy metaphor for organization (CEO → VPs → Directors → Managers → ICs), agents can take on any role or job title needed for your specific project - from Software Engineers and Data Scientists to Game Designers, Research Analysts, Content Writers, or Domain Specialists. The system features:

- **Startup Discovery Phase**: Dynamically generates 5 discovery questions via OpenAI (mocked in CI)
- **Dynamic Organization Planning**: Generates org structure based on project needs and budget
- **Budget Management**: CFO monitors spending with soft/hard caps and automatic downgrades
- **OKR/KPI Tracking**: Metrics rollup through organizational hierarchy
- **Live Execution**: Watch tasks execute with real-time progress and budget updates
- **JSON-Patch Updates**: Dynamic plan adjustments as conditions change

## Installation

```bash
# Install from PyPI
pip install plugah>=0.2

# Or using uv (recommended for development)
uv pip install plugah>=0.2
```

## Quick Start

### CLI Demo

```bash
plugah-demo --prompt "Build a Slack bot that summarizes conversations" --budget 100
```

### Python API

```python
import asyncio
from plugah import BoardRoom, BudgetPolicy

async def main():
    # Initialize the board room
    br = BoardRoom()
    
    # Phase 1: Generate discovery questions (OpenAI-driven; mocked if PLUGAH_MODE=mock)
    questions = await br.startup_phase(
        problem="Build a Slack summarizer bot",
        budget_usd=100.0,
        policy=BudgetPolicy.BALANCED
    )
    
    # Phase 2: Process answers into PRD
    answers = [
        "Developers and data scientists",
        "Accurate summaries, Fast processing, Easy integration",
        "Must handle rate limits, Secure API keys",
        "2 weeks",
        "Slack API"
    ]
    prd = await br.process_discovery(
        answers=answers,
        problem="Build a Slack summarizer bot",
        budget_usd=100.0
    )
    
    # Phase 3: Plan organization structure
    oag = await br.plan_organization(
        prd=prd,
        budget_usd=100.0,
        policy=BudgetPolicy.BALANCED
    )
    
    # Phase 4: Execute the plan
    result = await br.execute()
    
    print(f"Project complete! Total cost: ${result.total_cost}")
    print(f"Artifacts: {result.artifacts}")
    print(f"Metrics: {result.metrics}")

asyncio.run(main())
```

### ReOrg (Update PRD and Replan)

```python
from plugah import BoardRoom, PRD

br = BoardRoom()
# ... run discovery and planning first ...
updated = PRD({
    "title": "New Direction",
    "problem_statement": "Updated scope",
    "budget": 150.0,
    "objectives": [],
})
br.reorg(updated)  # rewrites PRD.md + team PRDs and replans the OAG
```

### State Persistence

```python
# Save state between phases
br = BoardRoom()
questions = await br.startup_phase(problem, budget)
br.save_state("project_state.json")

# Later, restore and continue
br2 = BoardRoom()
br2.load_state("project_state.json")
prd = await br2.process_discovery(answers, problem, budget)
```

### Mock Mode for CI/Testing

```bash
# Enable mock mode (no API calls, deterministic outputs)
export PLUGAH_MODE=mock
python your_script.py
```

## Web Interface

Start the web interface for an interactive experience:

```bash
# Start backend
cd web/backend
uvicorn main:app --reload

# In another terminal, start frontend
cd web/frontend
npm install
npm run dev
```

Visit http://localhost:5173 to:
1. Enter your project prompt and budget
2. Answer discovery questions
3. Watch the org chart generate
4. Monitor live execution with budget tracking
5. View OKR/KPI progress in real-time

## Core Concepts

### Organizational Agent Graph (OAG)

The OAG represents your virtual organization:
- **Nodes**: Agents (with dynamically assigned roles) and Tasks (work items)
- **Edges**: Collaboration relationships and task dependencies
- **Contracts**: Explicit input/output specifications for each task
- **Budget Model**: Soft/hard caps with policy (conservative/balanced/aggressive)

The graph structure adapts to your project - a web development project might have Frontend Engineers reporting to a UI/UX Lead, while a research project could have Data Scientists collaborating with Domain Experts.

### PRD Artifacts

Plugah writes human-readable PRD documents to keep agents aligned:
- Root PRD: `.runs/<project_id>/PRD.md` (overview, objectives, plus OKR/KPI roll-up tables after planning)
- Team PRDs: `.runs/<project_id>/teams/<agent_id>/PRD.md` (inherits parent PRD, links back via `../../PRD.md`, and lists team OKRs/KPIs and roll-ups)

The Board Room can “ReOrg” at any time: update the PRD, re-plan, and rewrite PRD docs.

### Agent Organization

The system uses a hierarchical structure as an organizational metaphor, but agents adapt to your project's needs:

- **C-Suite Level**: Strategic oversight and budget control (can be CEO, Lead Architect, Principal Investigator, etc.)
- **VP Level**: Department or domain leadership (VP Engineering, Head of Research, Creative Director, etc.)
- **Director Level**: Team coordination (Engineering Director, QA Lead, Design Lead, etc.)
- **Manager Level**: Task planning and delegation (Sprint Manager, Project Coordinator, etc.)
- **IC Level**: Specialized execution (Software Engineers, Data Scientists, Writers, Designers, Analysts, or any domain-specific role)

The actual roles and specializations are dynamically determined based on your project requirements. For example:
- A game development project might spawn Game Designers, Level Artists, and Gameplay Programmers
- A research project could create Research Scientists, Data Analysts, and Literature Review Specialists
- A content project might generate Content Writers, SEO Specialists, and Fact Checkers

### Budget Policies

- **Conservative**: Minimal staffing, economy models, essential tools only
- **Balanced**: Moderate staffing, standard models, standard toolset
- **Aggressive**: Full staffing, premium models, all available tools

### Metrics System

- **OKRs**: Objectives and Key Results owned by agents
- **KPIs**: Key Performance Indicators tracked per role
- **Rollups**: Metrics aggregate up the management chain
- **Health Scores**: Overall project health based on multiple factors

## Architecture

```
plugah/
├── orchestrator.py    # Stable public API (BoardRoom)
├── types.py           # Public types (ExecutionResult, PRD, exceptions)
├── oag_schema.py      # Pydantic models for the org graph
├── boardroom.py       # Internal orchestrator with C-suite
├── planner.py         # Creates org structure from PRD
├── executor.py        # Runs tasks with budget gates
├── budget.py          # CFO logic and cost control
├── metrics.py         # OKR/KPI tracking and rollups
├── materialize.py     # Converts to CrewAI agents
└── tools/             # Tool implementations (research, code, data, etc.)
```

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev,demo]"

# Run tests
pytest

# Type checking
mypy plugah

# Linting
ruff check plugah

# Pre-commit hooks (mirror CI):
pre-commit install
pre-commit run --all-files
```

## Configuration

### Budget Policies

```python
from plugah import BoardRoom, BudgetPolicy

br = BoardRoom()

# Use different policies for different phases
questions = await br.startup_phase(
    problem="...",
    budget_usd=100.0,
    policy=BudgetPolicy.CONSERVATIVE  # Save money during discovery
)

oag = await br.plan_organization(
    prd=prd,
    budget_usd=100.0,
    policy=BudgetPolicy.AGGRESSIVE  # Maximize resources for execution
)
```

### Event Streaming

```python
# Get execution events
async def handle_event(event, data):
    print(f"Event: {event.value}, Data: {data}")

result = await br.execute(on_event=handle_event)

# Or iterate over events
async for event in br.events_stream():
    print(f"Phase: {event.phase}, Cost: ${event.acc_cost}")
```

### Exception Handling

```python
from plugah import InvalidInput, BudgetExceeded, ProviderError

try:
    result = await br.execute()
except BudgetExceeded as e:
    print(f"Budget exceeded: {e.details}")
except InvalidInput as e:
    print(f"Invalid input: {e.details}")
except ProviderError as e:
    print(f"Provider error: {e.details}")
```

## Examples

See the `examples/` directory for:
- Building a web scraper
- Creating a data pipeline
- Developing a REST API
- Training an ML model

## Contributing

- We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and setup.
- Please review our [Code of Conduct](CODE_OF_CONDUCT.md).
- Security issues? See our [Security Policy](SECURITY.md).
- For a concise contributor quickstart, read [AGENTS.md](AGENTS.md).
 - When opening issues, include an agent-ready prompt (Cursor/Claude Code/Codex); templates are provided.

## License

MIT License - see LICENSE file for details.

## Credits

Built with:
- [CrewAI](https://github.com/joaomdmoura/crewAI) - Multi-agent framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [React](https://react.dev/) - Frontend framework

---

**Note**: This is an experimental project exploring multi-agent orchestration patterns. The organizational hierarchy is used as a metaphor for structuring agent collaboration - the actual agents can take on any role or specialization needed for your project. These are AI agents, not real people. Actual costs depend on your LLM provider pricing.
### LLM Configuration

- Set `OPENAI_API_KEY` in your environment to enable OpenAI calls.
- Optionally set `OPENAI_MODEL` or `DEFAULT_LLM_MODEL` to override the default model (`gpt-5-nano`).
 - The executor performs a brief "reasoning" call per task to guide execution; when using CrewAI, the reasoning is prepended to the task description to inform the agent.
 - CrewAI execution is enabled by default. To force mock execution only, set `PLUGAH_REAL_EXECUTION=0` (or `false`/`no`).

Example:

```bash
export OPENAI_API_KEY=sk-...  # required for live LLM calls
export OPENAI_MODEL=gpt-5-nano
# optional: disable CrewAI and force mock execution
export PLUGAH_REAL_EXECUTION=0
pytest  # or run your program
```
