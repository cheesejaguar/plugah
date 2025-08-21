"""
Plans OAG from problem description and discovery answers
"""

import uuid
from typing import Any

from .oag_schema import (
    KPI,
    OAG,
    OKR,
    AgentSpec,
    BudgetCaps,
    BudgetModel,
    BudgetPolicy,
    Contract,
    ContractIO,
    CostTrack,
    Direction,
    Edge,
    KeyResult,
    Objective,
    OrgMeta,
    RoleLevel,
    TaskSpec,
    TaskStatus,
)
from .selector import Selector


class Planner:
    """Plans organizational structure and task graph"""

    def __init__(self, selector: Selector | None = None):
        self.selector = selector or Selector()

    def plan(
        self, prd: dict[str, Any], budget_usd: float, context: dict[str, Any] | None = None
    ) -> OAG:
        """Create an OAG from PRD and budget"""

        context = context or {}
        project_id = str(uuid.uuid4())

        # Extract from PRD
        project_title = prd.get("title", "Project")
        domain = prd.get("domain", "general")
        objectives = prd.get("objectives", [])
        # constraints = prd.get("constraints", [])  # For future use
        success_criteria = prd.get("success_criteria", [])

        # Determine budget policy
        policy = self._determine_budget_policy(budget_usd, len(objectives))

        # Create metadata
        meta = OrgMeta(project_id=project_id, title=project_title, domain=domain)

        # Create budget model
        budget = BudgetModel(
            caps=BudgetCaps(soft_cap_usd=budget_usd * 0.8, hard_cap_usd=budget_usd),
            policy=policy,
            forecast_cost_usd=0.0,
        )

        # Initialize OAG
        oag = OAG(meta=meta, budget=budget, nodes={}, edges=[])

        # Create Board Room
        self._create_board_room(oag, project_title, domain, objectives)

        # Determine staffing
        staffing = self.selector.determine_staffing_level(
            scope_size=self._estimate_scope_size(objectives), budget=budget_usd, domain=domain
        )

        # Create organizational hierarchy
        vps = self._create_vps(oag, project_title, domain, staffing["vps"])
        directors = self._create_directors(oag, project_title, domain, vps, staffing["directors"])
        managers = self._create_managers(
            oag, project_title, domain, directors, staffing["managers"]
        )
        ics = self._create_ics(oag, project_title, domain, managers, staffing["ics"])

        # Create tasks based on objectives
        tasks = self._create_tasks(oag, objectives, success_criteria, ics)

        # Create edges
        self._create_task_dependencies(oag, tasks)

        # Calculate forecast
        oag.budget.forecast_cost_usd = self._forecast_cost(oag)

        return oag

    def _determine_budget_policy(self, budget: float, num_objectives: int) -> BudgetPolicy:
        """Determine budget policy based on budget and scope"""

        if budget < 20 or num_objectives > 5:
            return BudgetPolicy.CONSERVATIVE
        elif budget > 100 and num_objectives <= 3:
            return BudgetPolicy.AGGRESSIVE
        else:
            return BudgetPolicy.BALANCED

    def _estimate_scope_size(self, objectives: list[dict]) -> str:
        """Estimate project scope size"""

        num_objectives = len(objectives)
        if num_objectives <= 2:
            return "small"
        elif num_objectives <= 5:
            return "medium"
        else:
            return "large"

    def _create_board_room(self, oag: OAG, project_title: str, domain: str, objectives: list[dict]):
        """Create C-Suite executives"""

        # CEO
        ceo_id = "agent_ceo"
        ceo_okrs = self._create_okrs_for_role("CEO", objectives)

        ceo = AgentSpec(
            id=ceo_id,
            role="CEO",
            level=RoleLevel.C_SUITE,
            system_prompt=self.selector.compose_system_prompt(
                role="CEO",
                level=RoleLevel.C_SUITE,
                project_title=project_title,
                domain=domain,
                specialization=None,
                context={"objectives": objectives},
            ),
            tools=self.selector.select_tools(
                role="CEO",
                specialization=None,
                task_description="Strategic oversight",
                available_budget=oag.budget.caps.hard_cap_usd,
            ),
            llm=self.selector.select_model(RoleLevel.C_SUITE),
            okrs=ceo_okrs,
        )
        oag.add_node(ceo)

        # CTO
        cto_id = "agent_cto"
        cto_okrs = self._create_okrs_for_role("CTO", objectives)

        cto = AgentSpec(
            id=cto_id,
            role="CTO",
            level=RoleLevel.C_SUITE,
            system_prompt=self.selector.compose_system_prompt(
                role="CTO",
                level=RoleLevel.C_SUITE,
                project_title=project_title,
                domain=domain,
                specialization=None,
                context={"objectives": objectives},
            ),
            tools=self.selector.select_tools(
                role="CTO",
                specialization=None,
                task_description="Technical strategy",
                available_budget=oag.budget.caps.hard_cap_usd,
            ),
            llm=self.selector.select_model(RoleLevel.C_SUITE),
            okrs=cto_okrs,
        )
        oag.add_node(cto)

        # CFO
        cfo_id = "agent_cfo"
        cfo_kpis = [
            KPI(
                id="kpi_burn_rate",
                metric="Burn Rate",
                target=oag.budget.caps.soft_cap_usd / 10,
                direction=Direction.LTE,
                owner_agent_id=cfo_id,
            ),
            KPI(
                id="kpi_cost_efficiency",
                metric="Cost per Deliverable",
                target=oag.budget.caps.hard_cap_usd / max(len(objectives), 1),
                direction=Direction.LTE,
                owner_agent_id=cfo_id,
            ),
        ]

        cfo = AgentSpec(
            id=cfo_id,
            role="CFO",
            level=RoleLevel.C_SUITE,
            system_prompt=self.selector.compose_system_prompt(
                role="CFO",
                level=RoleLevel.C_SUITE,
                project_title=project_title,
                domain=domain,
                specialization=None,
                context={
                    "budget_soft_cap": oag.budget.caps.soft_cap_usd,
                    "budget_hard_cap": oag.budget.caps.hard_cap_usd,
                },
            ),
            tools=self.selector.select_tools(
                role="CFO",
                specialization=None,
                task_description="Budget management",
                available_budget=oag.budget.caps.hard_cap_usd,
            ),
            llm=self.selector.select_model(RoleLevel.C_SUITE),
            kpis=cfo_kpis,
        )
        oag.add_node(cfo)

    def _create_vps(self, oag: OAG, project_title: str, domain: str, count: int) -> list[str]:
        """Create VP-level positions"""

        vp_roles = ["VP Engineering", "VP Product", "VP Data"][:count]
        vp_ids = []

        for role in vp_roles:
            vp_id = f"agent_vp_{role.lower().replace(' ', '_')}"

            vp = AgentSpec(
                id=vp_id,
                role=role,
                level=RoleLevel.VP,
                manager_id="agent_ceo",
                specialization=self.selector.select_specialization(role, domain, ""),
                system_prompt=self.selector.compose_system_prompt(
                    role=role,
                    level=RoleLevel.VP,
                    project_title=project_title,
                    domain=domain,
                    specialization=None,
                    context={},
                ),
                tools=self.selector.select_tools(
                    role=role,
                    specialization=None,
                    task_description="Department leadership",
                    available_budget=oag.budget.caps.hard_cap_usd * 0.3,
                ),
                llm=self.selector.select_model(RoleLevel.VP),
            )
            oag.add_node(vp)
            vp_ids.append(vp_id)

        return vp_ids

    def _create_directors(
        self, oag: OAG, project_title: str, domain: str, vp_ids: list[str], count: int
    ) -> list[str]:
        """Create Director-level positions"""

        director_ids = []
        directors_per_vp = max(1, count // max(len(vp_ids), 1))

        for vp_id in vp_ids:
            for i in range(directors_per_vp):
                dir_id = f"agent_dir_{vp_id.split('_')[-1]}_{i}"

                director = AgentSpec(
                    id=dir_id,
                    role=f"Director {i + 1}",
                    level=RoleLevel.DIRECTOR,
                    manager_id=vp_id,
                    system_prompt=self.selector.compose_system_prompt(
                        role="Director",
                        level=RoleLevel.DIRECTOR,
                        project_title=project_title,
                        domain=domain,
                        specialization=None,
                        context={},
                    ),
                    tools=self.selector.select_tools(
                        role="Director",
                        specialization=None,
                        task_description="Team management",
                        available_budget=oag.budget.caps.hard_cap_usd * 0.1,
                    ),
                    llm=self.selector.select_model(RoleLevel.DIRECTOR),
                )
                oag.add_node(director)
                director_ids.append(dir_id)

        return director_ids

    def _create_managers(
        self, oag: OAG, project_title: str, domain: str, director_ids: list[str], count: int
    ) -> list[str]:
        """Create Manager-level positions"""

        manager_ids = []
        managers_per_director = max(1, count // max(len(director_ids), 1))

        for dir_id in director_ids:
            for i in range(managers_per_director):
                mgr_id = f"agent_mgr_{dir_id.split('_')[-2]}_{dir_id.split('_')[-1]}_{i}"

                manager = AgentSpec(
                    id=mgr_id,
                    role=f"Manager {i + 1}",
                    level=RoleLevel.MANAGER,
                    manager_id=dir_id,
                    system_prompt=self.selector.compose_system_prompt(
                        role="Manager",
                        level=RoleLevel.MANAGER,
                        project_title=project_title,
                        domain=domain,
                        specialization=None,
                        context={},
                    ),
                    tools=self.selector.select_tools(
                        role="Manager",
                        specialization=None,
                        task_description="Sprint management",
                        available_budget=oag.budget.caps.hard_cap_usd * 0.05,
                    ),
                    llm=self.selector.select_model(RoleLevel.MANAGER),
                )
                oag.add_node(manager)
                manager_ids.append(mgr_id)

        return manager_ids

    def _create_ics(
        self, oag: OAG, project_title: str, domain: str, manager_ids: list[str], count: int
    ) -> list[str]:
        """Create Individual Contributor positions"""

        ic_ids = []
        ics_per_manager = max(1, count // max(len(manager_ids), 1))

        ic_roles = ["Engineer", "Analyst", "Designer", "QA"]

        for mgr_id in manager_ids:
            for i in range(ics_per_manager):
                role = ic_roles[i % len(ic_roles)]
                ic_id = f"agent_ic_{mgr_id.split('_')[-1]}_{role.lower()}_{i}"

                specialization = self.selector.select_specialization(role, domain, "")

                ic = AgentSpec(
                    id=ic_id,
                    role=role,
                    level=RoleLevel.IC,
                    manager_id=mgr_id,
                    specialization=specialization,
                    system_prompt=self.selector.compose_system_prompt(
                        role=role,
                        level=RoleLevel.IC,
                        project_title=project_title,
                        domain=domain,
                        specialization=specialization,
                        context={},
                    ),
                    tools=self.selector.select_tools(
                        role=role,
                        specialization=specialization,
                        task_description="Implementation",
                        available_budget=oag.budget.caps.hard_cap_usd * 0.02,
                    ),
                    llm=self.selector.select_model(RoleLevel.IC),
                )
                oag.add_node(ic)
                ic_ids.append(ic_id)

        return ic_ids

    def _create_tasks(
        self, oag: OAG, objectives: list[dict], success_criteria: list[str], ic_ids: list[str]
    ) -> list[str]:
        """Create tasks from objectives"""

        task_ids = []

        # Standard tasks for any project
        standard_tasks = [
            ("Architecture Design", "Design system architecture", ["architecture_doc"]),
            ("Data Sourcing", "Identify and prepare data sources", ["data_sources"]),
            ("MVP Implementation", "Build minimum viable product", ["mvp_code"]),
            ("Testing", "Test and validate implementation", ["test_results"]),
            ("Documentation", "Create user and technical documentation", ["documentation"]),
            ("Deployment", "Deploy to production", ["deployment_status"]),
        ]

        for i, (task_name, description, outputs) in enumerate(standard_tasks):
            task_id = f"task_{task_name.lower().replace(' ', '_')}"
            agent_id = ic_ids[i % len(ic_ids)] if ic_ids else "agent_ic_0_engineer_0"

            # Create contract
            contract = Contract(
                inputs=[
                    ContractIO(
                        name="requirements",
                        dtype="string",
                        description="Project requirements",
                        required=True,
                    )
                ],
                outputs=[
                    ContractIO(
                        name=output,
                        dtype="string",
                        description=f"{task_name} output",
                        required=True,
                    )
                    for output in outputs
                ],
                definition_of_done=f"{task_name} completed and validated",
            )

            task = TaskSpec(
                id=task_id,
                description=description,
                agent_id=agent_id,
                contract=contract,
                expected_output=f"Completed {task_name.lower()}",
                status=TaskStatus.PLANNED,
                cost=CostTrack(est_cost_usd=self.selector.estimate_role_cost(RoleLevel.IC)),
            )

            oag.add_node(task)
            task_ids.append(task_id)

        return task_ids

    def _create_task_dependencies(self, oag: OAG, task_ids: list[str]):
        """Create edges between tasks"""

        # Simple linear dependencies for now
        for i in range(len(task_ids) - 1):
            edge = Edge(
                id=f"edge_{i}",
                from_id=task_ids[i],
                to_id=task_ids[i + 1],
                mapping={"output": "input"},
            )
            oag.add_edge(edge)

    def _create_okrs_for_role(self, role: str, objectives: list[dict]) -> list[OKR]:
        """Create OKRs for a specific role"""

        okrs = []

        if role == "CEO" and objectives:
            obj = Objective(
                id="obj_user_value",
                title="Deliver User Value",
                description="Ensure project delivers value to users",
                owner_agent_id="agent_ceo",
            )

            krs = [
                KeyResult(
                    id="kr_completion",
                    objective_id="obj_user_value",
                    metric="Project Completion",
                    target=100,
                    direction=Direction.GTE,
                ),
                KeyResult(
                    id="kr_quality",
                    objective_id="obj_user_value",
                    metric="Quality Score",
                    target=90,
                    direction=Direction.GTE,
                ),
            ]

            okrs.append(OKR(objective=obj, key_results=krs))

        elif role == "CTO":
            obj = Objective(
                id="obj_tech_excellence",
                title="Technical Excellence",
                description="Ensure technical quality and architecture",
                owner_agent_id="agent_cto",
            )

            krs = [
                KeyResult(
                    id="kr_architecture",
                    objective_id="obj_tech_excellence",
                    metric="Architecture Score",
                    target=95,
                    direction=Direction.GTE,
                )
            ]

            okrs.append(OKR(objective=obj, key_results=krs))

        return okrs

    def _forecast_cost(self, oag: OAG) -> float:
        """Calculate forecasted cost for the OAG"""

        total_cost = 0.0

        # Sum up agent costs (estimated per interaction)
        for agent in oag.get_agents().values():
            total_cost += (
                self.selector.estimate_role_cost(agent.level) * 10
            )  # Assume 10 interactions

        # Sum up task costs
        for task in oag.get_tasks().values():
            total_cost += task.cost.est_cost_usd

        return total_cost
