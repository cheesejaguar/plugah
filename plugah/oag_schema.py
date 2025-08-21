"""
Organizational Agent Graph (OAG) schema definitions using Pydantic v2
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class RoleLevel(str, Enum):
    C_SUITE = "C_SUITE"
    VP = "VP"
    DIRECTOR = "DIRECTOR"
    MANAGER = "MANAGER"
    IC = "IC"
    EXTERNAL = "EXTERNAL"


class NodeType(str, Enum):
    AGENT = "agent"
    TASK = "task"
    EXTERNAL = "external"


class TaskStatus(str, Enum):
    PLANNED = "planned"
    READY = "ready"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


class Direction(str, Enum):
    GTE = ">="
    LTE = "<="
    EQ = "="


class BudgetPolicy(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class Reusability(str, Enum):
    EXCLUSIVE = "exclusive"
    SHARED = "shared"


class OrgMeta(BaseModel):
    project_id: str
    title: str
    domain: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1


class Objective(BaseModel):
    id: str
    title: str
    description: str
    owner_agent_id: str


class KeyResult(BaseModel):
    id: str
    objective_id: str
    metric: str
    target: float | int
    current: float | int = 0
    direction: Direction = Direction.GTE


class OKR(BaseModel):
    objective: Objective
    key_results: list[KeyResult] = []


class KPI(BaseModel):
    id: str
    metric: str
    target: float | int
    current: float | int = 0
    direction: Direction = Direction.GTE
    owner_agent_id: str


class ContractIO(BaseModel):
    name: str
    dtype: str
    description: str
    required: bool = True


class Contract(BaseModel):
    inputs: list[ContractIO] = []
    outputs: list[ContractIO] = []
    definition_of_done: str


class ToolRef(BaseModel):
    id: str
    args: dict[str, Any] | None = None


class BudgetCaps(BaseModel):
    hard_cap_usd: float
    soft_cap_usd: float


class CostTrack(BaseModel):
    est_cost_usd: float = 0.0
    actual_cost_usd: float = 0.0
    token_estimate: int = 0


class AgentSpec(BaseModel):
    id: str
    role: str
    level: RoleLevel
    manager_id: str | None = None
    specialization: str | None = None
    system_prompt: str = ""
    tools: list[ToolRef] = []
    llm: str | None = None
    okrs: list[OKR] = []
    kpis: list[KPI] = []
    reusability: Reusability = Reusability.EXCLUSIVE
    node_type: Literal["agent"] = "agent"


class TaskSpec(BaseModel):
    id: str
    description: str
    agent_id: str
    contract: Contract
    expected_output: str
    status: TaskStatus = TaskStatus.PLANNED
    artifacts: dict[str, Any] = {}
    cost: CostTrack = Field(default_factory=CostTrack)
    dependencies: list[str] = []
    node_type: Literal["task"] = "task"


class Edge(BaseModel):
    id: str
    from_id: str
    to_id: str
    condition: str | None = None
    mapping: dict[str, str] = {}


class BudgetModel(BaseModel):
    caps: BudgetCaps
    forecast_cost_usd: float = 0.0
    actual_cost_usd: float = 0.0
    policy: BudgetPolicy = BudgetPolicy.BALANCED


class OAG(BaseModel):
    meta: OrgMeta
    budget: BudgetModel
    nodes: dict[str, AgentSpec | TaskSpec]
    edges: list[Edge] = []

    @field_validator("nodes")
    @classmethod
    def validate_node_types(cls, v):
        for node_id, node in v.items():
            if node_id != node.id:
                raise ValueError(f"Node ID mismatch: {node_id} != {node.id}")
        return v

    def get_agents(self) -> dict[str, AgentSpec]:
        return {k: v for k, v in self.nodes.items() if isinstance(v, AgentSpec)}

    def get_tasks(self) -> dict[str, TaskSpec]:
        return {k: v for k, v in self.nodes.items() if isinstance(v, TaskSpec)}

    def get_node(self, node_id: str) -> AgentSpec | TaskSpec | None:
        return self.nodes.get(node_id)

    def add_node(self, node: AgentSpec | TaskSpec):
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge):
        self.edges.append(edge)

    def get_dependencies(self, task_id: str) -> list[str]:
        deps = []
        for edge in self.edges:
            if edge.to_id == task_id:
                deps.append(edge.from_id)
        return deps

    def model_json_schema(self):
        return super().model_json_schema()


def validate_oag(oag_dict: dict) -> OAG:
    """Validate and parse an OAG dictionary"""
    return OAG.model_validate(oag_dict)
