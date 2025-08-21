"""
CFO utilities: cost estimation, hard/soft caps, spend telemetry
"""

from enum import Enum
from typing import Any

from .oag_schema import BudgetModel, BudgetPolicy, RoleLevel


class BudgetAlert(Enum):
    NORMAL = "normal"
    WARNING = "warning"  # 70% of soft cap
    CRITICAL = "critical"  # 90% of soft cap
    EXCEEDED_SOFT = "exceeded_soft"  # Over soft cap
    EMERGENCY = "emergency"  # 90% of hard cap


class BudgetManager:
    """Manage budget, track spending, and enforce caps"""

    def __init__(self, budget: BudgetModel):
        self.budget = budget
        self.spent = 0.0
        self.spend_history: list[dict[str, Any]] = []
        self.alerts: list[dict[str, Any]] = []

    def record_spend(self, amount: float, description: str = "") -> bool:
        """
        Record a spend amount
        
        Returns:
            True if spend was recorded, False if it would exceed hard cap
        """

        if self.spent + amount > self.budget.caps.hard_cap_usd:
            self._add_alert(BudgetAlert.EMERGENCY, f"Spend would exceed hard cap: ${amount}")
            return False

        self.spent += amount
        self.budget.actual_cost_usd = self.spent

        self.spend_history.append({
            "amount": amount,
            "description": description,
            "total_spent": self.spent,
            "remaining": self.get_remaining()
        })

        # Check alert thresholds
        self._check_alerts()

        return True

    def get_spent(self) -> float:
        """Get total spent amount"""
        return self.spent

    def get_remaining(self) -> float:
        """Get remaining budget before hard cap"""
        return self.budget.caps.hard_cap_usd - self.spent

    def get_soft_cap_remaining(self) -> float:
        """Get remaining budget before soft cap"""
        return self.budget.caps.soft_cap_usd - self.spent

    def can_proceed(self) -> bool:
        """Check if execution can proceed within budget"""
        return self.spent < self.budget.caps.hard_cap_usd

    def is_near_soft_cap(self, threshold: float = 0.9) -> bool:
        """Check if spending is near soft cap"""
        return self.spent >= self.budget.caps.soft_cap_usd * threshold

    def is_near_hard_cap(self, threshold: float = 0.9) -> bool:
        """Check if spending is near hard cap"""
        return self.spent >= self.budget.caps.hard_cap_usd * threshold

    def get_alert_level(self) -> BudgetAlert:
        """Get current budget alert level"""

        soft_cap = self.budget.caps.soft_cap_usd
        hard_cap = self.budget.caps.hard_cap_usd

        if self.spent >= hard_cap * 0.9:
            return BudgetAlert.EMERGENCY
        elif self.spent >= soft_cap:
            return BudgetAlert.EXCEEDED_SOFT
        elif self.spent >= soft_cap * 0.9:
            return BudgetAlert.CRITICAL
        elif self.spent >= soft_cap * 0.7:
            return BudgetAlert.WARNING
        else:
            return BudgetAlert.NORMAL

    def _check_alerts(self):
        """Check and record budget alerts"""

        alert_level = self.get_alert_level()

        if alert_level != BudgetAlert.NORMAL:
            self._add_alert(alert_level, f"Budget alert: {alert_level.value}")

    def _add_alert(self, level: BudgetAlert, message: str):
        """Add a budget alert"""

        self.alerts.append({
            "level": level,
            "message": message,
            "spent": self.spent,
            "soft_cap": self.budget.caps.soft_cap_usd,
            "hard_cap": self.budget.caps.hard_cap_usd
        })

    def get_recommendations(self) -> list[str]:
        """Get cost optimization recommendations based on current state"""

        recommendations = []
        alert_level = self.get_alert_level()

        if alert_level == BudgetAlert.EMERGENCY:
            recommendations.extend([
                "URGENT: Halt all non-critical operations",
                "Downgrade all models to economy tier",
                "Disable expensive tools",
                "Consider reducing scope immediately"
            ])
        elif alert_level == BudgetAlert.EXCEEDED_SOFT:
            recommendations.extend([
                "Soft cap exceeded - implement cost controls",
                "Switch to conservative budget policy",
                "Reduce team size for remaining tasks",
                "Use economy models for all ICs"
            ])
        elif alert_level == BudgetAlert.CRITICAL:
            recommendations.extend([
                "Approaching soft cap - prepare contingencies",
                "Consider deferring non-essential tasks",
                "Downgrade models for non-critical roles",
                "Limit tool usage to essentials"
            ])
        elif alert_level == BudgetAlert.WARNING:
            recommendations.extend([
                "Monitor spending closely",
                "Review task priorities",
                "Consider model optimization"
            ])

        return recommendations

    def forecast_completion_cost(self, tasks_remaining: int, avg_cost_per_task: float) -> float:
        """Forecast total cost to complete remaining tasks"""

        forecast = self.spent + (tasks_remaining * avg_cost_per_task)
        return forecast

    def can_afford_task(self, estimated_cost: float) -> bool:
        """Check if a task can be afforded within budget"""

        return self.spent + estimated_cost <= self.budget.caps.hard_cap_usd

    def suggest_model_tier(self) -> str:
        """Suggest appropriate model tier based on budget status"""

        alert_level = self.get_alert_level()

        if alert_level in [BudgetAlert.EMERGENCY, BudgetAlert.EXCEEDED_SOFT]:
            return "economy"
        elif alert_level == BudgetAlert.CRITICAL:
            return "standard"
        else:
            # Use policy-based selection
            if self.budget.policy == BudgetPolicy.CONSERVATIVE:
                return "economy"
            elif self.budget.policy == BudgetPolicy.AGGRESSIVE:
                return "premium"
            else:
                return "standard"


class CostEstimator:
    """Estimate costs for various operations"""

    # Model costs per 1k tokens (approximate)
    MODEL_COSTS = {
        "gpt-4-turbo": 0.01,
        "gpt-3.5-turbo": 0.002,
        "gpt-3.5-turbo-instruct": 0.0015
    }

    # Average tokens per interaction by role level
    TOKENS_BY_LEVEL = {
        RoleLevel.C_SUITE: 2000,
        RoleLevel.VP: 1500,
        RoleLevel.DIRECTOR: 1000,
        RoleLevel.MANAGER: 800,
        RoleLevel.IC: 500,
        RoleLevel.EXTERNAL: 600
    }

    @classmethod
    def estimate_task_cost(
        cls,
        role_level: RoleLevel,
        model: str,
        num_interactions: int = 1
    ) -> float:
        """Estimate cost for a task"""

        tokens = cls.TOKENS_BY_LEVEL.get(role_level, 500)
        model_cost = cls.MODEL_COSTS.get(model, 0.002)

        # Cost = (tokens / 1000) * cost_per_1k * interactions
        cost = (tokens / 1000) * model_cost * num_interactions

        return cost

    @classmethod
    def estimate_oag_cost(cls, oag: Any) -> float:
        """Estimate total cost for an OAG"""

        total_cost = 0.0

        # Estimate agent costs
        for agent in oag.get_agents().values():
            model = agent.llm or "gpt-3.5-turbo"
            # Assume 5 interactions per agent
            cost = cls.estimate_task_cost(agent.level, model, 5)
            total_cost += cost

        # Estimate task costs
        for task in oag.get_tasks().values():
            # Use estimated cost from task spec
            total_cost += task.cost.est_cost_usd

        return total_cost

    @classmethod
    def estimate_tool_cost(cls, tool_id: str, uses: int = 1) -> float:
        """Estimate cost for tool usage"""

        # Simple model: different costs per tool
        tool_costs = {
            "web_search": 0.05,
            "code_reader": 0.01,
            "data_tool": 0.03,
            "writer": 0.01,
            "qa_tool": 0.02
        }

        cost_per_use = tool_costs.get(tool_id, 0.01)
        return cost_per_use * uses


class CFO:
    """CFO agent for budget management and cost control"""

    def __init__(self, budget_manager: BudgetManager):
        self.budget_manager = budget_manager
        self.cost_estimator = CostEstimator()

    def evaluate_spend_request(
        self,
        amount: float,
        purpose: str,
        priority: str = "medium"
    ) -> dict[str, Any]:
        """Evaluate a spending request"""

        can_afford = self.budget_manager.can_afford_task(amount)
        alert_level = self.budget_manager.get_alert_level()

        # Decision logic
        approved = False
        reason = ""

        if not can_afford:
            reason = "Would exceed hard budget cap"
        elif alert_level == BudgetAlert.EMERGENCY:
            reason = "Emergency budget state - only critical spending allowed"
            approved = (priority == "critical")
        elif alert_level == BudgetAlert.EXCEEDED_SOFT:
            reason = "Soft cap exceeded - high priority only"
            approved = (priority in ["critical", "high"])
        elif alert_level == BudgetAlert.CRITICAL:
            reason = "Near soft cap - reviewing carefully"
            approved = (priority != "low")
        else:
            approved = True
            reason = "Within budget parameters"

        return {
            "approved": approved,
            "reason": reason,
            "amount": amount,
            "purpose": purpose,
            "priority": priority,
            "remaining_budget": self.budget_manager.get_remaining(),
            "recommendations": self.budget_manager.get_recommendations() if not approved else []
        }

    def generate_budget_patch(self) -> dict[str, Any]:
        """Generate a patch to adjust budget policy or caps"""

        alert_level = self.budget_manager.get_alert_level()

        if alert_level in [BudgetAlert.EMERGENCY, BudgetAlert.EXCEEDED_SOFT, BudgetAlert.CRITICAL]:
            # Switch to conservative policy when approaching or exceeding soft cap
            return {
                "op": "replace",
                "path": "/budget/policy",
                "value": "conservative"
            }
        elif alert_level == BudgetAlert.WARNING:
            # Adjust forecast at warning level
            return {
                "op": "replace",
                "path": "/budget/forecast_cost_usd",
                "value": self.budget_manager.spent * 1.2  # 20% buffer
            }

        return None
