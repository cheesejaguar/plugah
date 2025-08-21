# Plugah.ai 🧠

Multi-agent orchestration system with organizational hierarchy - dynamically generates and manages AI agent organizations to deliver projects within budget constraints.

## Overview

Plugah.ai creates a virtual company of AI agents organized in a realistic hierarchy (CEO → VPs → Directors → Managers → ICs) to tackle complex projects. The system features:

- **Startup Discovery Phase**: Co-founders interview you to understand requirements
- **Dynamic Organization Planning**: Generates org structure based on project needs and budget
- **Budget Management**: CFO monitors spending with soft/hard caps and automatic downgrades
- **OKR/KPI Tracking**: Metrics rollup through organizational hierarchy
- **Live Execution**: Watch tasks execute with real-time progress and budget updates
- **JSON-Patch Updates**: Dynamic plan adjustments as conditions change

## Installation

```bash
# Using uv (recommended)
uv pip install plugah

# Or using pip
pip install plugah
```

## Quick Start

### CLI Demo

```bash
plugah-demo --prompt "Build a Slack bot that summarizes conversations" --budget 100
```

### Python API

```python
import asyncio
from plugah import BoardRoom, Startup

async def main():
    # Initialize the board room
    boardroom = BoardRoom()
    
    # Run startup discovery
    discovery = await boardroom.startup_phase(
        problem="Build a Slack summarizer bot",
        budget_usd=100.0
    )
    
    # Answer discovery questions
    answers = [
        "Developers and data scientists",
        "Accurate summaries, Fast processing, Easy integration",
        "Must handle rate limits, Secure API keys",
        "2 weeks",
        "Slack API"
    ]
    
    # Generate PRD
    prd = await boardroom.process_discovery(answers, problem, budget_usd)
    
    # Plan organization
    oag = await boardroom.plan_organization(prd, budget_usd)
    
    # Execute
    results = await boardroom.execute()
    
    print(f"Project complete! Total cost: ${results['total_cost']}")

asyncio.run(main())
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

The OAG represents your virtual company:
- **Nodes**: Agents (employees) and Tasks (work items)
- **Edges**: Reporting relationships and task dependencies
- **Contracts**: Explicit input/output specifications for each task
- **Budget Model**: Soft/hard caps with policy (conservative/balanced/aggressive)

### Role Hierarchy

- **C-Suite** (CEO, CTO, CFO): Strategic decisions, budget control
- **VPs**: Department leadership (Engineering, Product, Data)
- **Directors**: Team management and coordination
- **Managers**: Sprint planning and execution
- **ICs**: Individual contributors doing the work

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
├── oag_schema.py      # Pydantic models for the org graph
├── boardroom.py       # Main orchestrator with C-suite
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
```

## Configuration

Set budget limits and policies in your code:

```python
from plugah import BudgetPolicy

# Configure budget
budget_caps = {
    "soft_cap_usd": 80.0,  # Warning at 70%, downgrades at 90%
    "hard_cap_usd": 100.0  # Absolute maximum
}

# Set policy
policy = BudgetPolicy.BALANCED  # or CONSERVATIVE, AGGRESSIVE
```

## Examples

See the `examples/` directory for:
- Building a web scraper
- Creating a data pipeline
- Developing a REST API
- Training an ML model

## Contributing

We welcome contributions! Please see CONTRIBUTING.md for guidelines.

## License

MIT License - see LICENSE file for details.

## Credits

Built with:
- [CrewAI](https://github.com/joaomdmoura/crewAI) - Multi-agent framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [React](https://react.dev/) - Frontend framework

---

**Note**: This is an experimental project exploring multi-agent orchestration patterns. The virtual "employees" are AI agents, not real people. Actual costs depend on your LLM provider pricing.