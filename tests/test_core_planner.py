from plugah.core.models import BudgetPolicy
from plugah.core.planner import OrgPlanner


def test_planner_team_sizes_policy():
    p = OrgPlanner()
    org_bal = p.plan("prd1", BudgetPolicy.BALANCED, problem="Generic project")
    org_cheap = p.plan("prd1", BudgetPolicy.CHEAP, problem="Generic project")
    org_fast = p.plan("prd1", BudgetPolicy.FAST, problem="Generic project")

    assert len(org_cheap.ics) <= len(org_bal.ics)
    assert len(org_fast.ics) >= len(org_bal.ics)
    assert len(org_fast.ics) <= 6

