"""
Selection logic for specializations, tools, prompts, models, and staffing
"""

from typing import Any

from .oag_schema import RoleLevel, ToolRef
from .registry import TOOL_REGISTRY, ToolSelector, get_specialization_for_domain
from .templates import compose_system_prompt


class Selector:
    """Central selector for all agent configuration decisions"""

    def __init__(self, budget_policy: str = "balanced"):
        self.budget_policy = budget_policy
        self.tool_selector = ToolSelector()

    def select_specialization(
        self, role: str, domain: str | None, task_description: str
    ) -> str | None:
        """Select appropriate specialization for a role"""

        # First try domain-specific specialization
        if domain:
            spec = get_specialization_for_domain(domain, role)
            if spec:
                return spec

        # Fallback to role-based defaults
        role_specializations = {
            "Engineer": "Software Engineer",
            "Manager": "Engineering Manager",
            "Analyst": "Product Analyst",
            "Designer": "UX Designer",
            "Architect": "Tech Architect",
            "Lead": "Tech Lead",
        }

        for key, spec in role_specializations.items():
            if key.lower() in role.lower():
                return spec

        return None

    def select_tools(
        self, role: str, specialization: str | None, task_description: str, available_budget: float
    ) -> list[ToolRef]:
        """Select tools for an agent"""

        # Use specialization if available, otherwise role
        lookup_role = specialization or role

        tool_ids = self.tool_selector.select_tools(
            role=lookup_role,
            task_description=task_description,
            budget_policy=self.budget_policy,
            available_budget=available_budget,
        )

        # Convert to ToolRef objects
        tools = []
        for tool_id in tool_ids:
            if tool_id in TOOL_REGISTRY:
                tools.append(ToolRef(id=tool_id))

        return tools

    def select_model(self, role_level: RoleLevel, task_complexity: str = "medium") -> str:
        """Select appropriate LLM model"""

        return self.tool_selector.select_model(
            role_level=role_level.value,
            budget_policy=self.budget_policy,
            task_complexity=task_complexity,
        )

    def compose_system_prompt(
        self,
        role: str,
        level: RoleLevel,
        project_title: str,
        domain: str | None,
        specialization: str | None,
        context: dict[str, Any],
    ) -> str:
        """Compose full system prompt for an agent"""

        return compose_system_prompt(
            role=role,
            level=level.value,
            project_title=project_title,
            domain=domain,
            specialization=specialization,
            context=context,
        )

    def determine_staffing_level(
        self, scope_size: str, budget: float, domain: str | None
    ) -> dict[str, int]:
        """Determine how many of each role type to hire"""

        if self.budget_policy == "conservative":
            # Minimal staffing
            return {
                "vps": 1,  # Just VP Eng
                "directors": 1,
                "managers": 1,
                "ics": 2,
            }
        elif self.budget_policy == "aggressive":
            # Full staffing
            return {
                "vps": 3,  # VP Eng, VP Product, VP Data
                "directors": 4,
                "managers": 6,
                "ics": 12,
            }
        else:  # balanced
            # Moderate staffing based on budget
            if budget < 50:
                return {"vps": 1, "directors": 2, "managers": 2, "ics": 4}
            elif budget < 200:
                return {"vps": 2, "directors": 3, "managers": 4, "ics": 8}
            else:
                return {"vps": 3, "directors": 4, "managers": 5, "ics": 10}

    def estimate_role_cost(self, role_level: RoleLevel) -> float:
        """Estimate cost per task for a role level"""

        # Base cost by level
        level_costs = {
            RoleLevel.C_SUITE: 1.0,
            RoleLevel.VP: 0.5,
            RoleLevel.DIRECTOR: 0.3,
            RoleLevel.MANAGER: 0.2,
            RoleLevel.IC: 0.1,
            RoleLevel.EXTERNAL: 0.15,
        }

        base_cost = level_costs.get(role_level, 0.1)

        # Adjust by policy
        if self.budget_policy == "conservative":
            return base_cost * 0.7
        elif self.budget_policy == "aggressive":
            return base_cost * 1.5
        else:
            return base_cost
