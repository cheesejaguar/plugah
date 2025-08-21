"""
Plugah.ai - Multi-agent orchestration system with organizational hierarchy
"""

__version__ = "0.2.0"

from .oag_schema import BudgetPolicy, OAG
from .orchestrator import BoardRoom
from .types import (
    BudgetExceeded,
    Event,
    ExecutionResult,
    InvalidInput,
    PlugahError,
    PRD,
    ProviderError,
)

__all__ = [
    "BoardRoom",
    "BudgetPolicy",
    "BudgetExceeded",
    "Event",
    "ExecutionResult",
    "InvalidInput",
    "OAG",
    "PlugahError",
    "PRD",
    "ProviderError",
]
