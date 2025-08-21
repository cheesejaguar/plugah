"""
Converts OAG into CrewAI Agent & Task instances
"""

import os
from typing import Any

from crewai import Agent, Crew, Task

from .cache import get_cache
from .oag_schema import OAG, AgentSpec, TaskSpec, RoleLevel
from .registry import TOOL_REGISTRY


class Materializer:
    """Convert OAG specifications into executable CrewAI components"""

    def __init__(self):
        self.tool_cache = {}
        self.cache_manager = get_cache()

    def materialize(
        self, oag: OAG, llm_provider: str | None = None
    ) -> tuple[dict[str, Agent], dict[str, Task], dict[str, Any]]:
        """
        Materialize an OAG into CrewAI agents and tasks

        Returns:
            - agents: Dict mapping agent_id to CrewAI Agent
            - tasks: Dict mapping task_id to CrewAI Task
            - id_map: Additional mappings for tracking
        """

        agents = {}
        tasks = {}
        id_map = {}

        # Materialize agents
        for agent_id, agent_spec in oag.get_agents().items():
            agent = self._materialize_agent(oag, agent_spec, llm_provider)
            agents[agent_id] = agent
            id_map[agent_id] = {"type": "agent", "crewai_obj": agent, "spec": agent_spec}

        # Materialize tasks
        for task_id, task_spec in oag.get_tasks().items():
            # Get the assigned agent
            agent = agents.get(task_spec.agent_id)
            if not agent:
                # Create a default agent if missing
                agent = self._create_default_agent(oag, task_spec.agent_id)
                agents[task_spec.agent_id] = agent

            task = self._materialize_task(task_spec, agent, oag)
            tasks[task_id] = task
            id_map[task_id] = {"type": "task", "crewai_obj": task, "spec": task_spec}

        return agents, tasks, id_map

    def _materialize_agent(
        self, oag: OAG, spec: AgentSpec, llm_provider: str | None = None
    ) -> Agent:
        """Convert AgentSpec to CrewAI Agent"""

        # Load tools
        tools = []
        for tool_ref in spec.tools:
            tool = self._load_tool(tool_ref.id, tool_ref.args)
            if tool:
                tools.append(tool)

        # Create role string with level and specialization
        role_str = f"{spec.role}"
        if spec.specialization:
            role_str = f"{spec.specialization} ({spec.role})"

        # Ensure a non-empty, role-specific system prompt
        system_prompt = (spec.system_prompt or "").strip()
        if not system_prompt:
            from .selector import Selector

            selector = Selector()
            try:
                system_prompt = selector.compose_system_prompt(
                    role=spec.role,
                    level=spec.level,
                    project_title=oag.meta.title,
                    domain=oag.meta.domain,
                    specialization=spec.specialization,
                    context={},
                )
            except Exception:
                system_prompt = f"You are a {spec.level.value} {spec.role} for {oag.meta.title}. Execute tasks precisely to the definition of done."

        # Get LLM config from environment (prefer explicit model on spec)
        llm_model = spec.llm or os.getenv("DEFAULT_LLM_MODEL", "gpt-5-nano")

        # Create agent
        agent = Agent(
            role=role_str,
            goal=self._extract_goal_from_prompt(spec.system_prompt),
            backstory=self._create_backstory(spec),
            tools=tools,
            llm=llm_model,
            max_iter=5,
            verbose=True,
            allow_delegation=(spec.level.value in ["C_SUITE", "VP", "DIRECTOR"]),
            system_template=system_prompt,
        )

        return agent

    def _materialize_task(self, spec: TaskSpec, agent: Agent, oag: OAG) -> Task:
        """Convert TaskSpec to CrewAI Task"""

        # Build context from dependencies
        context_tasks = []
        # dependencies = oag.get_dependencies(spec.id)  # For future use

        # Create task description with contract
        description = self._build_task_description(spec)

        task = Task(
            description=description,
            expected_output=spec.expected_output,
            agent=agent,
            context=context_tasks,
            output_file=f".runs/{oag.meta.project_id}/{spec.id}/output.json",
        )

        return task

    def _load_tool(self, tool_id: str, args: dict | None = None) -> Any | None:
        """Load a tool from the registry"""

        # Check cache
        cache_key = f"{tool_id}_{args!s}"
        if cache_key in self.tool_cache:
            return self.tool_cache[cache_key]

        # Get tool definition
        tool_def = TOOL_REGISTRY.get(tool_id)
        if not tool_def:
            return None

        # Create a proper CrewAI tool wrapper with caching
        from crewai.tools import BaseTool

        cache_manager = self.cache_manager

        class CachedDynamicTool(BaseTool):
            name: str = tool_id
            description: str = tool_def.description

            def _run(self, *args, **kwargs):
                # Check cache first
                cache_data = {"tool": tool_id, "args": args, "kwargs": kwargs}

                cached_result = cache_manager.get(f"tool_{tool_id}", cache_data)
                if cached_result is not None:
                    return cached_result

                # Execute tool (in production, this would call actual tool logic)
                result = f"Tool {tool_id} executed with args: {args}, kwargs: {kwargs}"

                # Cache the result
                cache_manager.set(f"tool_{tool_id}", cache_data, result)

                return result

        tool = CachedDynamicTool()
        self.tool_cache[cache_key] = tool
        return tool

    def _create_default_agent(self, oag: OAG, agent_id: str) -> Agent:
        """Create a default agent for tasks without assigned agents"""
        from .selector import Selector

        selector = Selector()
        try:
            sys_tmpl = selector.compose_system_prompt(
                role="Default Worker",
                level=RoleLevel.IC,
                project_title=oag.meta.title,
                domain=oag.meta.domain,
                specialization="Software Engineer",
                context={},
            )
        except Exception:
            sys_tmpl = f"You are a Default Worker for {oag.meta.title}. Complete assigned tasks accurately."

        return Agent(
            role="Default Worker",
            goal="Complete assigned tasks",
            backstory="A diligent worker ready to tackle any task",
            tools=[],
            llm=os.getenv("DEFAULT_LLM_MODEL", "gpt-5-nano"),
            max_iter=3,
            verbose=True,
            system_template=sys_tmpl,
        )

    def _extract_goal_from_prompt(self, system_prompt: str) -> str:
        """Extract a goal from the system prompt"""

        lines = system_prompt.split("\n")
        for line in lines:
            if "responsibility" in line.lower() or "must" in line.lower():
                return line.strip()

        return "Achieve project objectives"

    def _create_backstory(self, spec: AgentSpec) -> str:
        """Create a backstory for an agent"""

        backstory = f"As a {spec.level.value.replace('_', ' ').title()}-level {spec.role}"

        if spec.specialization:
            backstory += f" specializing in {spec.specialization}"

        if spec.okrs:
            backstory += f", you own {len(spec.okrs)} key objectives"

        if spec.kpis:
            backstory += f" and track {len(spec.kpis)} KPIs"

        backstory += ". You bring expertise and leadership to ensure success."

        return backstory

    def _build_task_description(self, spec: TaskSpec) -> str:
        """Build a comprehensive task description including contract"""

        desc = f"{spec.description}\n\n"

        if spec.contract.inputs:
            desc += "Required Inputs:\n"
            for inp in spec.contract.inputs:
                req = "required" if inp.required else "optional"
                desc += f"- {inp.name} ({inp.dtype}, {req}): {inp.description}\n"
            desc += "\n"

        if spec.contract.outputs:
            desc += "Expected Outputs:\n"
            for out in spec.contract.outputs:
                req = "required" if out.required else "optional"
                desc += f"- {out.name} ({out.dtype}, {req}): {out.description}\n"
            desc += "\n"

        desc += f"Definition of Done: {spec.contract.definition_of_done}"

        return desc


class CrewBuilder:
    """Build CrewAI Crew from materialized components"""

    @staticmethod
    def build_crew(agents: dict[str, Agent], tasks: dict[str, Task], oag: OAG) -> Crew:
        """Build a CrewAI Crew from agents and tasks"""

        # Order tasks by dependencies
        ordered_tasks = CrewBuilder._order_tasks(tasks, oag)

        # Get unique agents
        unique_agents = list(agents.values())

        crew = Crew(
            agents=unique_agents,
            tasks=ordered_tasks,
            verbose=2,
            process="sequential",  # Could be "hierarchical" for complex orgs
        )

        return crew

    @staticmethod
    def _order_tasks(tasks: dict[str, Task], oag: OAG) -> list[Task]:
        """Order tasks based on dependencies"""

        import networkx as nx

        # Build dependency graph
        g = nx.DiGraph()

        for task_id in tasks.keys():
            g.add_node(task_id)

        for edge in oag.edges:
            if edge.from_id in tasks and edge.to_id in tasks:
                g.add_edge(edge.from_id, edge.to_id)

        # Topological sort
        try:
            ordered_ids = list(nx.topological_sort(g))
        except nx.NetworkXError:
            # Cycle detected, use original order
            ordered_ids = list(tasks.keys())

        # Return tasks in order
        return [tasks[tid] for tid in ordered_ids if tid in tasks]
