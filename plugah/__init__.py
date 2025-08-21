"""
Plugah.ai - Multi-agent orchestration system with organizational hierarchy
"""

__version__ = "0.2.0"

from .oag_schema import OAG, BudgetPolicy
from .orchestrator import BoardRoom
from .types import (
    PRD,
    BudgetExceeded,
    Event,
    ExecutionResult,
    InvalidInput,
    PlugahError,
    ProviderError,
)

__all__ = [
    "OAG",
    "PRD",
    "BoardRoom",
    "BudgetExceeded",
    "BudgetPolicy",
    "Event",
    "ExecutionResult",
    "InvalidInput",
    "PlugahError",
    "ProviderError",
]
