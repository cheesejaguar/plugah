"""
DAG execution with budget gates and progress callbacks
"""

import asyncio
import time
from typing import Dict, List, Callable, Optional, Any
from enum import Enum
import networkx as nx
from .oag_schema import OAG, TaskSpec, TaskStatus, AgentSpec
from .materialize import Materializer, CrewBuilder
from .budget import BudgetManager


class ExecutionEvent(Enum):
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    BUDGET_WARNING = "budget_warning"
    BUDGET_EXCEEDED = "budget_exceeded"
    PATCH_APPLIED = "patch_applied"
    KPI_UPDATE = "kpi_update"
    OKR_UPDATE = "okr_update"


class ExecutionResult:
    """Result of a task execution"""
    
    def __init__(
        self,
        task_id: str,
        status: TaskStatus,
        output: Any = None,
        error: Optional[str] = None,
        cost: float = 0.0,
        duration: float = 0.0
    ):
        self.task_id = task_id
        self.status = status
        self.output = output
        self.error = error
        self.cost = cost
        self.duration = duration


class Executor:
    """Execute OAG with budget control and event callbacks"""
    
    def __init__(
        self,
        oag: OAG,
        budget_manager: Optional[BudgetManager] = None,
        materializer: Optional[Materializer] = None
    ):
        self.oag = oag
        self.budget_manager = budget_manager or BudgetManager(oag.budget)
        self.materializer = materializer or Materializer()
        self.callbacks: List[Callable] = []
        self.execution_graph = None
        self.results: Dict[str, ExecutionResult] = {}
    
    def add_callback(self, callback: Callable):
        """Add an event callback"""
        self.callbacks.append(callback)
    
    def _emit_event(self, event: ExecutionEvent, data: Dict[str, Any]):
        """Emit an event to all callbacks"""
        for callback in self.callbacks:
            try:
                callback(event, data)
            except Exception as e:
                print(f"Callback error: {e}")
    
    async def execute(self, parallel: bool = True) -> Dict[str, ExecutionResult]:
        """
        Execute the OAG
        
        Args:
            parallel: Whether to execute independent tasks in parallel
        
        Returns:
            Dictionary of task_id -> ExecutionResult
        """
        
        # Build execution graph
        self.execution_graph = self._build_execution_graph()
        
        # Materialize agents and tasks
        agents, tasks, id_map = self.materializer.materialize(self.oag)
        
        # Check initial budget
        if not self.budget_manager.can_proceed():
            self._emit_event(ExecutionEvent.BUDGET_EXCEEDED, {
                "message": "Budget exceeded before execution",
                "spent": self.budget_manager.get_spent(),
                "limit": self.budget_manager.budget.caps.hard_cap_usd
            })
            return {}
        
        # Execute in waves
        if parallel:
            await self._execute_parallel(tasks)
        else:
            await self._execute_sequential(tasks)
        
        return self.results
    
    def _build_execution_graph(self) -> nx.DiGraph:
        """Build execution graph from OAG"""
        
        G = nx.DiGraph()
        
        # Add all tasks
        for task_id, task_spec in self.oag.get_tasks().items():
            G.add_node(task_id, spec=task_spec)
        
        # Add dependencies
        for edge in self.oag.edges:
            if edge.from_id in G and edge.to_id in G:
                G.add_edge(edge.from_id, edge.to_id, edge=edge)
        
        return G
    
    async def _execute_sequential(self, tasks: Dict[str, Any]):
        """Execute tasks sequentially in dependency order"""
        
        # Get topological order
        try:
            task_order = list(nx.topological_sort(self.execution_graph))
        except nx.NetworkXError:
            # Handle cycles
            task_order = list(tasks.keys())
        
        for task_id in task_order:
            if task_id not in tasks:
                continue
            
            # Check if dependencies are satisfied
            if not self._dependencies_satisfied(task_id):
                result = ExecutionResult(
                    task_id=task_id,
                    status=TaskStatus.SKIPPED,
                    error="Dependencies not satisfied"
                )
                self.results[task_id] = result
                continue
            
            # Execute task
            await self._execute_task(task_id, tasks[task_id])
    
    async def _execute_parallel(self, tasks: Dict[str, Any]):
        """Execute tasks in parallel waves based on dependencies"""
        
        remaining_tasks = set(tasks.keys())
        
        while remaining_tasks:
            # Find tasks that can be executed now
            ready_tasks = []
            for task_id in remaining_tasks:
                if self._dependencies_satisfied(task_id):
                    ready_tasks.append(task_id)
            
            if not ready_tasks:
                # No tasks ready, might be a cycle
                break
            
            # Execute ready tasks in parallel
            coroutines = [
                self._execute_task(task_id, tasks[task_id])
                for task_id in ready_tasks
            ]
            
            await asyncio.gather(*coroutines)
            
            # Remove completed tasks
            for task_id in ready_tasks:
                remaining_tasks.remove(task_id)
    
    def _dependencies_satisfied(self, task_id: str) -> bool:
        """Check if all dependencies of a task are satisfied"""
        
        if task_id not in self.execution_graph:
            return True
        
        for pred in self.execution_graph.predecessors(task_id):
            if pred not in self.results:
                return False
            if self.results[pred].status != TaskStatus.DONE:
                return False
        
        return True
    
    async def _execute_task(self, task_id: str, task: Any):
        """Execute a single task"""
        
        # Get task spec
        task_spec = self.oag.get_node(task_id)
        if not isinstance(task_spec, TaskSpec):
            return
        
        # Check budget before execution
        if not self.budget_manager.can_proceed():
            self._emit_event(ExecutionEvent.BUDGET_EXCEEDED, {
                "task_id": task_id,
                "spent": self.budget_manager.get_spent()
            })
            
            result = ExecutionResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error="Budget exceeded"
            )
            self.results[task_id] = result
            return
        
        # Emit start event
        self._emit_event(ExecutionEvent.TASK_START, {
            "task_id": task_id,
            "description": task_spec.description,
            "agent_id": task_spec.agent_id
        })
        
        # Update task status
        task_spec.status = TaskStatus.RUNNING
        
        start_time = time.time()
        
        try:
            # Simulate task execution (in production, would call CrewAI)
            await asyncio.sleep(0.5)  # Simulate work
            
            # Mock output
            output = {
                "result": f"Completed {task_spec.description}",
                "artifacts": {"data": "sample"}
            }
            
            # Calculate cost
            cost = task_spec.cost.est_cost_usd
            
            # Update budget
            self.budget_manager.record_spend(cost)
            
            # Check for budget warnings
            if self.budget_manager.is_near_soft_cap():
                self._emit_event(ExecutionEvent.BUDGET_WARNING, {
                    "task_id": task_id,
                    "spent": self.budget_manager.get_spent(),
                    "soft_cap": self.budget_manager.budget.caps.soft_cap_usd
                })
            
            # Update task
            task_spec.status = TaskStatus.DONE
            task_spec.artifacts = output.get("artifacts", {})
            task_spec.cost.actual_cost_usd = cost
            
            # Create result
            result = ExecutionResult(
                task_id=task_id,
                status=TaskStatus.DONE,
                output=output,
                cost=cost,
                duration=time.time() - start_time
            )
            
            # Emit complete event
            self._emit_event(ExecutionEvent.TASK_COMPLETE, {
                "task_id": task_id,
                "output": output,
                "cost": cost,
                "duration": result.duration
            })
            
        except Exception as e:
            # Task failed
            task_spec.status = TaskStatus.FAILED
            
            result = ExecutionResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                duration=time.time() - start_time
            )
            
            self._emit_event(ExecutionEvent.TASK_FAILED, {
                "task_id": task_id,
                "error": str(e)
            })
        
        self.results[task_id] = result
    
    def get_progress(self) -> Dict[str, Any]:
        """Get execution progress"""
        
        total_tasks = len(self.oag.get_tasks())
        completed_tasks = sum(
            1 for r in self.results.values()
            if r.status == TaskStatus.DONE
        )
        failed_tasks = sum(
            1 for r in self.results.values()
            if r.status == TaskStatus.FAILED
        )
        
        return {
            "total": total_tasks,
            "completed": completed_tasks,
            "failed": failed_tasks,
            "in_progress": total_tasks - completed_tasks - failed_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "total_cost": sum(r.cost for r in self.results.values()),
            "budget_remaining": self.budget_manager.get_remaining()
        }


class WaveExecutor(Executor):
    """Execute tasks in dependency waves"""
    
    async def execute(self, parallel: bool = True) -> Dict[str, ExecutionResult]:
        """Execute tasks in waves based on dependency levels"""
        
        # Build execution graph
        self.execution_graph = self._build_execution_graph()
        
        # Calculate waves
        waves = self._calculate_waves()
        
        # Materialize agents and tasks
        agents, tasks, id_map = self.materializer.materialize(self.oag)
        
        # Execute each wave
        for wave_num, wave_tasks in enumerate(waves):
            print(f"Executing wave {wave_num + 1} with {len(wave_tasks)} tasks")
            
            if parallel:
                # Execute wave tasks in parallel
                coroutines = [
                    self._execute_task(task_id, tasks.get(task_id))
                    for task_id in wave_tasks
                    if task_id in tasks
                ]
                await asyncio.gather(*coroutines)
            else:
                # Execute wave tasks sequentially
                for task_id in wave_tasks:
                    if task_id in tasks:
                        await self._execute_task(task_id, tasks[task_id])
            
            # Check budget after each wave
            if not self.budget_manager.can_proceed():
                print("Budget exceeded, stopping execution")
                break
        
        return self.results
    
    def _calculate_waves(self) -> List[List[str]]:
        """Calculate execution waves based on dependencies"""
        
        waves = []
        remaining = set(self.execution_graph.nodes())
        
        while remaining:
            # Find nodes with no dependencies in remaining set
            wave = []
            for node in remaining:
                predecessors = set(self.execution_graph.predecessors(node))
                if not predecessors.intersection(remaining):
                    wave.append(node)
            
            if not wave:
                # Cycle detected, add remaining nodes
                wave = list(remaining)
            
            waves.append(wave)
            remaining -= set(wave)
        
        return waves