"""
Tests for budget management
"""

import pytest
from plugah.budget import BudgetManager, BudgetAlert, CostEstimator, CFO
from plugah.oag_schema import BudgetModel, BudgetCaps, BudgetPolicy, RoleLevel


def test_budget_manager_tracking():
    """Test budget spend tracking"""
    
    budget_model = BudgetModel(
        caps=BudgetCaps(soft_cap_usd=80.0, hard_cap_usd=100.0),
        policy=BudgetPolicy.BALANCED
    )
    
    manager = BudgetManager(budget_model)
    
    # Record some spending
    assert manager.record_spend(10.0, "Task 1")
    assert manager.get_spent() == 10.0
    assert manager.get_remaining() == 90.0
    
    # Record more
    assert manager.record_spend(20.0, "Task 2")
    assert manager.get_spent() == 30.0
    assert manager.get_remaining() == 70.0


def test_budget_caps_enforcement():
    """Test that hard cap is enforced"""
    
    budget_model = BudgetModel(
        caps=BudgetCaps(soft_cap_usd=80.0, hard_cap_usd=100.0)
    )
    
    manager = BudgetManager(budget_model)
    
    # Spend up to near hard cap
    assert manager.record_spend(95.0, "Big task")
    
    # This should fail - would exceed hard cap
    assert not manager.record_spend(10.0, "Too much")
    assert manager.get_spent() == 95.0  # Unchanged


def test_budget_alert_levels():
    """Test budget alert level calculation"""
    
    budget_model = BudgetModel(
        caps=BudgetCaps(soft_cap_usd=80.0, hard_cap_usd=100.0)
    )
    
    manager = BudgetManager(budget_model)
    
    # Normal state
    assert manager.get_alert_level() == BudgetAlert.NORMAL
    
    # Warning at 70% of soft cap (56)
    manager.record_spend(56.0)
    assert manager.get_alert_level() == BudgetAlert.WARNING
    
    # Critical at 90% of soft cap (72)
    manager.record_spend(16.0)  # Total: 72
    assert manager.get_alert_level() == BudgetAlert.CRITICAL
    
    # Exceeded soft cap
    manager.record_spend(9.0)  # Total: 81
    assert manager.get_alert_level() == BudgetAlert.EXCEEDED_SOFT
    
    # Emergency at 90% of hard cap (90)
    manager.record_spend(9.0)  # Total: 90
    assert manager.get_alert_level() == BudgetAlert.EMERGENCY


def test_cfo_downgrade_on_soft_cap():
    """Test CFO downgrades models when approaching soft cap"""
    
    budget_model = BudgetModel(
        caps=BudgetCaps(soft_cap_usd=50.0, hard_cap_usd=100.0)
    )
    
    manager = BudgetManager(budget_model)
    cfo = CFO(manager)
    
    # Spend close to soft cap
    manager.record_spend(45.0)
    
    # CFO should recommend downgrades
    patch = cfo.generate_budget_patch()
    assert patch is not None
    assert patch["path"] == "/budget/policy"
    assert patch["value"] == "conservative"


def test_cfo_spend_approval():
    """Test CFO approval logic for spending requests"""
    
    budget_model = BudgetModel(
        caps=BudgetCaps(soft_cap_usd=50.0, hard_cap_usd=100.0)
    )
    
    manager = BudgetManager(budget_model)
    cfo = CFO(manager)
    
    # Normal state - should approve
    result = cfo.evaluate_spend_request(5.0, "New feature", "medium")
    assert result["approved"] == True
    
    # Spend up to critical
    manager.record_spend(46.0)  # 92% of soft cap
    
    # Should only approve high priority
    result_low = cfo.evaluate_spend_request(5.0, "Nice to have", "low")
    assert result_low["approved"] == False
    
    result_high = cfo.evaluate_spend_request(5.0, "Critical fix", "high")
    assert result_high["approved"] == True


def test_cost_estimator():
    """Test cost estimation for different role levels"""
    
    # C-suite should be most expensive
    c_suite_cost = CostEstimator.estimate_task_cost(
        RoleLevel.C_SUITE,
        "gpt-4-turbo",
        num_interactions=1
    )
    
    # IC should be cheapest
    ic_cost = CostEstimator.estimate_task_cost(
        RoleLevel.IC,
        "gpt-3.5-turbo",
        num_interactions=1
    )
    
    assert c_suite_cost > ic_cost
    
    # More interactions = more cost
    single_cost = CostEstimator.estimate_task_cost(
        RoleLevel.MANAGER,
        "gpt-3.5-turbo",
        num_interactions=1
    )
    
    multi_cost = CostEstimator.estimate_task_cost(
        RoleLevel.MANAGER,
        "gpt-3.5-turbo",
        num_interactions=5
    )
    
    assert multi_cost == single_cost * 5