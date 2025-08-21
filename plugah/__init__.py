"""
Plugah.ai - Multi-agent orchestration system with organizational hierarchy
"""

__version__ = "0.1.0"

from .oag_schema import (
    OAG,
    AgentSpec,
    TaskSpec,
    Edge,
    OKR,
    KPI,
    Contract,
    RoleLevel,
    NodeType,
    BudgetModel,
)
from .planner import Planner
from .selector import Selector
from .materialize import Materializer
from .executor import Executor
from .boardroom import BoardRoom, Startup
from .metrics import MetricsEngine
from .budget import BudgetManager

__all__ = [
    "OAG",
    "AgentSpec",
    "TaskSpec",
    "Edge",
    "OKR",
    "KPI",
    "Contract",
    "RoleLevel",
    "NodeType",
    "BudgetModel",
    "Planner",
    "Selector",
    "Materializer",
    "Executor",
    "BoardRoom",
    "Startup",
    "MetricsEngine",
    "BudgetManager",
]