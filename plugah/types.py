"""
Public types and exceptions for the Plugah orchestrator
"""

from typing import Any


class PlugahError(Exception):
    """Base exception for all Plugah errors"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.details = details or {}


class InvalidInput(PlugahError):  # noqa: N818
    """Invalid input provided to a Plugah API"""

    pass


class BudgetExceeded(PlugahError):  # noqa: N818
    """Budget limits have been exceeded"""

    pass


class ProviderError(PlugahError):
    """Error communicating with LLM provider"""

    pass


class ExecutionResult:
    """Result of executing an OAG"""

    def __init__(
        self,
        total_cost: float,
        artifacts: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.total_cost = total_cost
        self.artifacts = artifacts or {}
        self.metrics = metrics or {}
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_cost": self.total_cost,
            "artifacts": self.artifacts,
            "metrics": self.metrics,
            "details": self.details,
        }


class PRD:
    """Product Requirements Document from discovery phase"""

    def __init__(self, data: dict[str, Any]):
        self._data = data

    def to_dict(self) -> dict[str, Any]:
        """Get dictionary representation"""
        return self._data.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PRD":
        """Create from dictionary"""
        return cls(data)

    @property
    def objectives(self) -> list[dict[str, Any]]:
        """Get objectives"""
        return self._data.get("objectives", [])

    @property
    def requirements(self) -> list[str]:
        """Get requirements"""
        return self._data.get("requirements", [])

    @property
    def milestones(self) -> list[dict[str, Any]]:
        """Get milestones"""
        return self._data.get("milestones", [])

    @property
    def risks(self) -> list[str]:
        """Get risks"""
        return self._data.get("risks", [])

    def get_json_schema(self) -> dict[str, Any]:
        """Get JSON schema for PRD"""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "problem_statement": {"type": "string"},
                "budget": {"type": "number"},
                "domain": {"type": "string"},
                "users": {"type": "string"},
                "success_criteria": {"type": "array", "items": {"type": "string"}},
                "constraints": {"type": "array", "items": {"type": "string"}},
                "timeline": {"type": "string"},
                "integrations": {"type": "string"},
                "objectives": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                        },
                        "required": ["id", "title", "description"],
                    },
                },
                "key_results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "objective_id": {"type": "string"},
                            "metric": {"type": "string"},
                            "target": {"type": "number"},
                            "current": {"type": "number"},
                            "unit": {"type": "string"},
                        },
                        "required": ["id", "objective_id", "metric", "target"],
                    },
                },
                "requirements": {"type": "array", "items": {"type": "string"}},
                "milestones": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "date": {"type": "string"},
                        },
                    },
                },
                "risks": {"type": "array", "items": {"type": "string"}},
                "non_goals": {"type": "array", "items": {"type": "string"}},
                "created_at": {"type": "string"},
            },
            "required": ["title", "problem_statement", "objectives"],
        }


class Event:
    """Execution event for streaming"""

    def __init__(
        self,
        phase: str,
        message: str,
        cost_delta: float = 0.0,
        acc_cost: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ):
        self.phase = phase
        self.message = message
        self.cost_delta = cost_delta
        self.acc_cost = acc_cost
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "phase": self.phase,
            "message": self.message,
            "cost_delta": self.cost_delta,
            "acc_cost": self.acc_cost,
            "metadata": self.metadata,
        }
