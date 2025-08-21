"""
Tool and role-template registry with capabilities, tags, and selectors
"""

from dataclasses import dataclass
from enum import Enum


class ToolCategory(str, Enum):
    RESEARCH = "research"
    CODE = "code"
    DATA = "data"
    WRITING = "writing"
    TESTING = "testing"
    MONITORING = "monitoring"
    COMMUNICATION = "communication"


@dataclass
class Tool:
    id: str
    module_path: str
    category: ToolCategory
    tags: list[str]
    cost_tier: int = 1  # 1=cheap, 2=moderate, 3=expensive
    description: str = ""


@dataclass
class RolePreferences:
    role: str
    preferred_tools: list[str]
    required_tools: list[str]
    excluded_tools: list[str]


# Tool Registry
TOOL_REGISTRY = {
    "web_search": Tool(
        id="web_search",
        module_path="plugah.tools.research:WebSearchTool",
        category=ToolCategory.RESEARCH,
        tags=["research", "discovery", "market-analysis"],
        cost_tier=2,
        description="Search the web for information"
    ),
    "code_reader": Tool(
        id="code_reader",
        module_path="plugah.tools.code:RepoReaderTool",
        category=ToolCategory.CODE,
        tags=["code", "analysis", "review"],
        cost_tier=1,
        description="Read and analyze code repositories"
    ),
    "code_chunker": Tool(
        id="code_chunker",
        module_path="plugah.tools.code:CodeChunkerTool",
        category=ToolCategory.CODE,
        tags=["code", "processing", "chunking"],
        cost_tier=1,
        description="Process large codebases into chunks"
    ),
    "data_tool": Tool(
        id="data_tool",
        module_path="plugah.tools.data:DataTool",
        category=ToolCategory.DATA,
        tags=["data", "csv", "sql", "analysis"],
        cost_tier=2,
        description="Process and analyze data"
    ),
    "writer": Tool(
        id="writer",
        module_path="plugah.tools.write:WriterTool",
        category=ToolCategory.WRITING,
        tags=["writing", "documentation", "content"],
        cost_tier=1,
        description="Generate written content and documentation"
    ),
    "qa_tool": Tool(
        id="qa_tool",
        module_path="plugah.tools.qa:QATool",
        category=ToolCategory.TESTING,
        tags=["testing", "qa", "validation"],
        cost_tier=2,
        description="Run tests and quality checks"
    ),
}


# Role-specific tool preferences
ROLE_PREFERENCES = {
    "CEO": RolePreferences(
        role="CEO",
        preferred_tools=["web_search", "writer"],
        required_tools=[],
        excluded_tools=["code_chunker"]
    ),
    "CTO": RolePreferences(
        role="CTO",
        preferred_tools=["code_reader", "qa_tool"],
        required_tools=[],
        excluded_tools=[]
    ),
    "CFO": RolePreferences(
        role="CFO",
        preferred_tools=["data_tool"],
        required_tools=[],
        excluded_tools=["code_reader", "code_chunker"]
    ),
    "VP_ENG": RolePreferences(
        role="VP Engineering",
        preferred_tools=["code_reader", "code_chunker", "qa_tool"],
        required_tools=["code_reader"],
        excluded_tools=[]
    ),
    "VP_PRODUCT": RolePreferences(
        role="VP Product",
        preferred_tools=["web_search", "writer", "data_tool"],
        required_tools=["writer"],
        excluded_tools=["code_chunker"]
    ),
    "VP_DATA": RolePreferences(
        role="VP Data",
        preferred_tools=["data_tool", "code_reader"],
        required_tools=["data_tool"],
        excluded_tools=[]
    ),
    "DIRECTOR_PM": RolePreferences(
        role="Director PM",
        preferred_tools=["writer", "web_search"],
        required_tools=[],
        excluded_tools=["code_chunker"]
    ),
    "SWE": RolePreferences(
        role="Software Engineer",
        preferred_tools=["code_reader", "code_chunker", "qa_tool"],
        required_tools=["code_reader"],
        excluded_tools=[]
    ),
    "DATA_SCIENTIST": RolePreferences(
        role="Data Scientist",
        preferred_tools=["data_tool", "code_reader"],
        required_tools=["data_tool"],
        excluded_tools=[]
    ),
    "QA_ENGINEER": RolePreferences(
        role="QA Engineer",
        preferred_tools=["qa_tool", "code_reader"],
        required_tools=["qa_tool"],
        excluded_tools=[]
    ),
}


# Model tiers based on cost
MODEL_TIERS = {
    "premium": {
        "name": "gpt-4-turbo",
        "cost_per_1k": 0.01,
        "capability": "high"
    },
    "standard": {
        "name": "gpt-3.5-turbo",
        "cost_per_1k": 0.002,
        "capability": "medium"
    },
    "economy": {
        "name": "gpt-3.5-turbo",
        "cost_per_1k": 0.001,
        "capability": "basic"
    }
}


class ToolSelector:
    """Select appropriate tools based on role, task, and budget"""

    @staticmethod
    def select_tools(
        role: str,
        task_description: str,
        budget_policy: str,
        available_budget: float
    ) -> list[str]:
        """Select tools for a role/task combination"""

        # Get role preferences
        prefs = ROLE_PREFERENCES.get(role.upper().replace(" ", "_"))
        if not prefs:
            # Default selection for unknown roles
            return ["web_search", "writer"]

        selected = []

        # Always include required tools
        selected.extend(prefs.required_tools)

        # Add preferred tools based on budget policy
        if budget_policy == "aggressive":
            # Use all preferred tools
            selected.extend(prefs.preferred_tools)
        elif budget_policy == "balanced":
            # Use most preferred tools, skip expensive ones if budget is tight
            for tool_id in prefs.preferred_tools:
                tool = TOOL_REGISTRY.get(tool_id)
                if tool and (available_budget > 10 or tool.cost_tier <= 2):
                    selected.append(tool_id)
        else:  # conservative
            # Only use essential tools
            for tool_id in prefs.preferred_tools[:2]:  # Max 2 tools
                tool = TOOL_REGISTRY.get(tool_id)
                if tool and tool.cost_tier == 1:
                    selected.append(tool_id)

        # Remove excluded tools
        selected = [t for t in selected if t not in prefs.excluded_tools]

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for tool in selected:
            if tool not in seen:
                seen.add(tool)
                unique.append(tool)

        return unique

    @staticmethod
    def select_model(
        role_level: str,
        budget_policy: str,
        task_complexity: str = "medium"
    ) -> str:
        """Select appropriate model based on role and budget"""

        if budget_policy == "conservative":
            return MODEL_TIERS["economy"]["name"]
        elif budget_policy == "aggressive":
            return MODEL_TIERS["premium"]["name"]
        else:  # balanced
            # C-suite and VPs get better models
            if role_level in ["C_SUITE", "VP"]:
                return MODEL_TIERS["premium"]["name"]
            elif role_level in ["DIRECTOR", "MANAGER"]:
                return MODEL_TIERS["standard"]["name"]
            else:
                return MODEL_TIERS["economy"]["name"]

    @staticmethod
    def estimate_tool_cost(tool_ids: list[str]) -> float:
        """Estimate cost for using a set of tools"""

        total_cost = 0.0
        for tool_id in tool_ids:
            tool = TOOL_REGISTRY.get(tool_id)
            if tool:
                # Simple cost model: tier 1 = $0.01, tier 2 = $0.05, tier 3 = $0.10
                cost_map = {1: 0.01, 2: 0.05, 3: 0.10}
                total_cost += cost_map.get(tool.cost_tier, 0.01)

        return total_cost


def get_specialization_for_domain(domain: str, role: str) -> Optional[str]:
    """Get appropriate specialization based on domain and role"""

    domain_specializations = {
        "web": {
            "Engineer": "Frontend Engineer",
            "Manager": "Product Manager",
            "Director": "Director of Engineering"
        },
        "data": {
            "Engineer": "Data Engineer",
            "Scientist": "Data Scientist",
            "Manager": "Data Manager"
        },
        "api": {
            "Engineer": "Backend Engineer",
            "Architect": "Tech Architect",
            "Manager": "Engineering Manager"
        },
        "mobile": {
            "Engineer": "Mobile Engineer",
            "Designer": "UX Designer",
            "Manager": "Product Manager"
        }
    }

    domain_map = domain_specializations.get(domain.lower(), {})

    # Try to match role keywords
    for key, specialization in domain_map.items():
        if key.lower() in role.lower():
            return specialization

    return None
