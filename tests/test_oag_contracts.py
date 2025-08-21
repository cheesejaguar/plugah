"""
Tests for OAG contracts and schema validation
"""

import pytest
from pydantic import ValidationError
from plugah.oag_schema import (
    OAG, AgentSpec, TaskSpec, Contract, ContractIO,
    RoleLevel, TaskStatus, validate_oag, OrgMeta, BudgetModel, BudgetCaps
)


def test_contract_validation():
    """Test that contracts are properly validated"""
    
    # Valid contract
    contract = Contract(
        inputs=[
            ContractIO(name="input1", dtype="string", description="Test input", required=True)
        ],
        outputs=[
            ContractIO(name="output1", dtype="json", description="Test output", required=True)
        ],
        definition_of_done="Task is complete when output is generated"
    )
    
    assert len(contract.inputs) == 1
    assert len(contract.outputs) == 1
    assert contract.definition_of_done != ""


def test_agent_spec_validation():
    """Test AgentSpec validation"""
    
    agent = AgentSpec(
        id="agent_1",
        role="Engineer",
        level=RoleLevel.IC,
        system_prompt="You are an engineer"
    )
    
    assert agent.id == "agent_1"
    assert agent.level == RoleLevel.IC
    assert agent.node_type == "agent"


def test_task_spec_validation():
    """Test TaskSpec validation"""
    
    contract = Contract(
        inputs=[],
        outputs=[],
        definition_of_done="Complete the task"
    )
    
    task = TaskSpec(
        id="task_1",
        description="Build feature",
        agent_id="agent_1",
        contract=contract,
        expected_output="Feature built"
    )
    
    assert task.id == "task_1"
    assert task.status == TaskStatus.PLANNED
    assert task.node_type == "task"


def test_oag_validation():
    """Test complete OAG validation"""
    
    meta = OrgMeta(
        project_id="proj_1",
        title="Test Project",
        domain="web"
    )
    
    budget = BudgetModel(
        caps=BudgetCaps(soft_cap_usd=80.0, hard_cap_usd=100.0)
    )
    
    agent = AgentSpec(
        id="agent_1",
        role="CEO",
        level=RoleLevel.C_SUITE,
        system_prompt="Lead the company"
    )
    
    oag = OAG(
        meta=meta,
        budget=budget,
        nodes={"agent_1": agent},
        edges=[]
    )
    
    assert oag.meta.project_id == "proj_1"
    assert len(oag.get_agents()) == 1
    assert len(oag.get_tasks()) == 0


def test_oag_node_id_consistency():
    """Test that node IDs must match dictionary keys"""
    
    meta = OrgMeta(
        project_id="proj_1",
        title="Test Project"
    )
    
    budget = BudgetModel(
        caps=BudgetCaps(soft_cap_usd=80.0, hard_cap_usd=100.0)
    )
    
    agent = AgentSpec(
        id="agent_1",
        role="CEO",
        level=RoleLevel.C_SUITE,
        system_prompt="Lead"
    )
    
    # This should raise validation error - key doesn't match ID
    with pytest.raises(ValidationError):
        OAG(
            meta=meta,
            budget=budget,
            nodes={"wrong_id": agent},  # Mismatch!
            edges=[]
        )


def test_validate_oag_function():
    """Test the validate_oag helper function"""
    
    oag_dict = {
        "meta": {
            "project_id": "test_123",
            "title": "Test Project",
            "domain": "api",
            "version": 1
        },
        "budget": {
            "caps": {
                "soft_cap_usd": 100.0,
                "hard_cap_usd": 150.0
            },
            "policy": "balanced"
        },
        "nodes": {
            "agent_ceo": {
                "id": "agent_ceo",
                "role": "CEO",
                "level": "C_SUITE",
                "system_prompt": "You are the CEO",
                "tools": [],
                "node_type": "agent"
            }
        },
        "edges": []
    }
    
    oag = validate_oag(oag_dict)
    assert oag.meta.project_id == "test_123"
    assert "agent_ceo" in oag.nodes


def test_edge_mapping_validation():
    """Test that edge mappings are validated"""
    
    from plugah.oag_schema import Edge
    
    edge = Edge(
        id="edge_1",
        from_id="task_1",
        to_id="task_2",
        mapping={"output_field": "input_field"}
    )
    
    assert edge.from_id == "task_1"
    assert edge.to_id == "task_2"
    assert "output_field" in edge.mapping