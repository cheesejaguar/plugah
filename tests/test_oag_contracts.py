"""
Tests for OAG contracts and schema validation
"""

import pytest
from pydantic import ValidationError

from plugah.oag_schema import (
    OAG,
    AgentSpec,
    BudgetCaps,
    BudgetModel,
    Contract,
    ContractIO,
    OrgMeta,
    RoleLevel,
    TaskSpec,
    TaskStatus,
    validate_oag,
)


def test_contract_validation():
    """Test that contracts are properly validated"""

    # Valid contract parsed from plain data; ContractIO.required defaults to True
    contract = Contract.model_validate(
        {
            "inputs": [{"name": "input1", "dtype": "string", "description": "Test input"}],
            "outputs": [{"name": "output1", "dtype": "json", "description": "Test output"}],
            "definition_of_done": "Task is complete when output is generated",
        }
    )

    assert isinstance(contract.inputs[0], ContractIO)
    assert contract.inputs[0].required is True
    assert contract.outputs[0].dtype == "json"

    # inputs/outputs default to empty lists
    assert Contract(definition_of_done="done").inputs == []

    # definition_of_done is mandatory
    with pytest.raises(ValidationError):
        Contract(inputs=[], outputs=[])

    # ContractIO requires name, dtype and description
    with pytest.raises(ValidationError):
        ContractIO(name="x", dtype="string")


def test_agent_spec_validation():
    """Test AgentSpec validation"""

    agent = AgentSpec(
        id="agent_1", role="Engineer", level=RoleLevel.IC, system_prompt="You are an engineer"
    )

    assert agent.id == "agent_1"
    assert agent.level == RoleLevel.IC
    assert agent.node_type == "agent"


def test_task_spec_validation():
    """Test TaskSpec validation"""

    contract = Contract(inputs=[], outputs=[], definition_of_done="Complete the task")

    task = TaskSpec(
        id="task_1",
        description="Build feature",
        agent_id="agent_1",
        contract=contract,
        expected_output="Feature built",
    )

    assert task.id == "task_1"
    assert task.status == TaskStatus.PLANNED
    assert task.node_type == "task"


def test_oag_validation():
    """Test complete OAG validation"""

    meta = OrgMeta(project_id="proj_1", title="Test Project", domain="web")

    budget = BudgetModel(caps=BudgetCaps(soft_cap_usd=80.0, hard_cap_usd=100.0))

    agent = AgentSpec(
        id="agent_1", role="CEO", level=RoleLevel.C_SUITE, system_prompt="Lead the company"
    )

    oag = OAG(meta=meta, budget=budget, nodes={"agent_1": agent}, edges=[])

    assert oag.meta.project_id == "proj_1"
    assert len(oag.get_agents()) == 1
    assert len(oag.get_tasks()) == 0


def test_oag_node_id_consistency():
    """Test that node IDs must match dictionary keys"""

    meta = OrgMeta(project_id="proj_1", title="Test Project")

    budget = BudgetModel(caps=BudgetCaps(soft_cap_usd=80.0, hard_cap_usd=100.0))

    agent = AgentSpec(id="agent_1", role="CEO", level=RoleLevel.C_SUITE, system_prompt="Lead")

    # This should raise validation error - key doesn't match ID
    with pytest.raises(ValidationError):
        OAG(
            meta=meta,
            budget=budget,
            nodes={"wrong_id": agent},  # Mismatch!
            edges=[],
        )


def test_validate_oag_function():
    """Test the validate_oag helper function"""

    oag_dict = {
        "meta": {"project_id": "test_123", "title": "Test Project", "domain": "api", "version": 1},
        "budget": {"caps": {"soft_cap_usd": 100.0, "hard_cap_usd": 150.0}, "policy": "balanced"},
        "nodes": {
            "agent_ceo": {
                "id": "agent_ceo",
                "role": "CEO",
                "level": "C_SUITE",
                "system_prompt": "You are the CEO",
                "tools": [],
                "node_type": "agent",
            }
        },
        "edges": [],
    }

    oag = validate_oag(oag_dict)
    assert oag.meta.project_id == "test_123"
    assert "agent_ceo" in oag.nodes


def test_edge_mapping_validation():
    """Test that edge mappings are validated and drive task dependencies"""

    from plugah.oag_schema import Edge

    edge = Edge(
        id="edge_1", from_id="task_1", to_id="task_2", mapping={"output_field": "input_field"}
    )
    assert edge.mapping == {"output_field": "input_field"}
    assert Edge(id="e", from_id="a", to_id="b").mapping == {}

    # Mapping values must be field names (strings)
    with pytest.raises(ValidationError):
        Edge(id="edge_2", from_id="task_1", to_id="task_2", mapping={"out": {"nested": 1}})

    # Edges define the dependency graph used by the OAG
    oag = OAG(
        meta=OrgMeta(project_id="p", title="T"),
        budget=BudgetModel(caps=BudgetCaps(soft_cap_usd=1.0, hard_cap_usd=2.0)),
        nodes={},
        edges=[edge, Edge(id="edge_3", from_id="task_0", to_id="task_2")],
    )
    assert oag.get_dependencies("task_2") == ["task_1", "task_0"]
    assert oag.get_dependencies("task_1") == []
