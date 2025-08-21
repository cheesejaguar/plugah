"""
OKR/KPI model, subtree rollups, health scoring
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict
from .oag_schema import OAG, OKR, KPI, AgentSpec, TaskSpec, Direction


class MetricsEngine:
    """Calculate and track OKRs and KPIs"""
    
    def __init__(self, oag: OAG):
        self.oag = oag
        self.kpi_values: Dict[str, float] = {}
        self.kr_values: Dict[str, float] = {}
        self.task_metrics: Dict[str, Dict[str, Any]] = {}
    
    def update_kpi(self, kpi_id: str, value: float):
        """Update a KPI value"""
        self.kpi_values[kpi_id] = value
    
    def update_key_result(self, kr_id: str, value: float):
        """Update a key result value"""
        self.kr_values[kr_id] = value
    
    def update_from_task(self, task_id: str, output: Dict[str, Any]):
        """Update metrics from task output"""
        
        self.task_metrics[task_id] = output
        
        # Extract metrics from output
        # This is simplified - in production would have more sophisticated parsing
        if "metrics" in output:
            for metric_name, value in output["metrics"].items():
                # Try to match to KPIs
                for agent in self.oag.get_agents().values():
                    for kpi in agent.kpis:
                        if metric_name.lower() in kpi.metric.lower():
                            self.update_kpi(kpi.id, value)
                    
                    # Try to match to KRs
                    for okr in agent.okrs:
                        for kr in okr.key_results:
                            if metric_name.lower() in kr.metric.lower():
                                self.update_key_result(kr.id, value)
    
    def calculate_okr_attainment(self, okr: OKR) -> float:
        """Calculate OKR attainment percentage"""
        
        if not okr.key_results:
            return 0.0
        
        total_attainment = 0.0
        for kr in okr.key_results:
            current = self.kr_values.get(kr.id, kr.current)
            
            if kr.direction == Direction.GTE:
                attainment = (current / kr.target) * 100 if kr.target > 0 else 0
            elif kr.direction == Direction.LTE:
                attainment = (kr.target / current) * 100 if current > 0 else 100
            else:  # EQ
                attainment = 100 if current == kr.target else 0
            
            # Cap at 100%
            attainment = min(attainment, 100)
            total_attainment += attainment
        
        return total_attainment / len(okr.key_results)
    
    def calculate_kpi_attainment(self, kpi: KPI) -> float:
        """Calculate KPI attainment percentage"""
        
        current = self.kpi_values.get(kpi.id, kpi.current)
        
        if kpi.direction == Direction.GTE:
            attainment = (current / kpi.target) * 100 if kpi.target > 0 else 0
        elif kpi.direction == Direction.LTE:
            attainment = (kpi.target / current) * 100 if current > 0 else 100
        else:  # EQ
            attainment = 100 if current == kpi.target else 0
        
        return min(attainment, 100)
    
    def calculate_rollups(self) -> Dict[str, Any]:
        """Calculate metric rollups by organizational hierarchy"""
        
        rollups = {
            "by_level": defaultdict(lambda: {"okr_attainment": [], "kpi_attainment": []}),
            "by_department": defaultdict(lambda: {"okr_attainment": [], "kpi_attainment": []}),
            "by_manager": defaultdict(lambda: {"okr_attainment": [], "kpi_attainment": []})
        }
        
        for agent_id, agent in self.oag.get_agents().items():
            # Calculate agent's metrics
            okr_attainments = [self.calculate_okr_attainment(okr) for okr in agent.okrs]
            kpi_attainments = [self.calculate_kpi_attainment(kpi) for kpi in agent.kpis]
            
            # Rollup by level
            level_key = agent.level.value
            if okr_attainments:
                rollups["by_level"][level_key]["okr_attainment"].extend(okr_attainments)
            if kpi_attainments:
                rollups["by_level"][level_key]["kpi_attainment"].extend(kpi_attainments)
            
            # Rollup by department (simplified - use role prefix)
            dept = agent.role.split()[0] if " " in agent.role else agent.role
            if okr_attainments:
                rollups["by_department"][dept]["okr_attainment"].extend(okr_attainments)
            if kpi_attainments:
                rollups["by_department"][dept]["kpi_attainment"].extend(kpi_attainments)
            
            # Rollup by manager
            if agent.manager_id:
                if okr_attainments:
                    rollups["by_manager"][agent.manager_id]["okr_attainment"].extend(okr_attainments)
                if kpi_attainments:
                    rollups["by_manager"][agent.manager_id]["kpi_attainment"].extend(kpi_attainments)
        
        # Calculate averages
        for category in rollups:
            for key in rollups[category]:
                okr_list = rollups[category][key]["okr_attainment"]
                kpi_list = rollups[category][key]["kpi_attainment"]
                
                rollups[category][key] = {
                    "okr_attainment": sum(okr_list) / len(okr_list) if okr_list else 0,
                    "kpi_attainment": sum(kpi_list) / len(kpi_list) if kpi_list else 0,
                    "okr_count": len(okr_list),
                    "kpi_count": len(kpi_list)
                }
        
        return dict(rollups)
    
    def calculate_health_score(self) -> Dict[str, float]:
        """Calculate overall health scores"""
        
        # Get all metrics
        all_okr_attainments = []
        all_kpi_attainments = []
        
        for agent in self.oag.get_agents().values():
            for okr in agent.okrs:
                all_okr_attainments.append(self.calculate_okr_attainment(okr))
            for kpi in agent.kpis:
                all_kpi_attainments.append(self.calculate_kpi_attainment(kpi))
        
        # Calculate task completion
        tasks = self.oag.get_tasks()
        completed_tasks = sum(1 for t in tasks.values() if t.status.value == "done")
        task_completion = (completed_tasks / len(tasks) * 100) if tasks else 0
        
        # Calculate budget health
        budget_health = 100
        if self.oag.budget.actual_cost_usd > 0:
            if self.oag.budget.actual_cost_usd > self.oag.budget.caps.hard_cap_usd:
                budget_health = 0
            elif self.oag.budget.actual_cost_usd > self.oag.budget.caps.soft_cap_usd:
                budget_health = 50
            else:
                budget_health = 100 - (
                    self.oag.budget.actual_cost_usd / self.oag.budget.caps.soft_cap_usd * 50
                )
        
        return {
            "overall": self._calculate_weighted_score([
                (sum(all_okr_attainments) / len(all_okr_attainments) if all_okr_attainments else 0, 0.3),
                (sum(all_kpi_attainments) / len(all_kpi_attainments) if all_kpi_attainments else 0, 0.3),
                (task_completion, 0.2),
                (budget_health, 0.2)
            ]),
            "okr_health": sum(all_okr_attainments) / len(all_okr_attainments) if all_okr_attainments else 0,
            "kpi_health": sum(all_kpi_attainments) / len(all_kpi_attainments) if all_kpi_attainments else 0,
            "task_health": task_completion,
            "budget_health": budget_health
        }
    
    def _calculate_weighted_score(self, scores_weights: List[tuple]) -> float:
        """Calculate weighted average score"""
        
        total_score = 0
        total_weight = 0
        
        for score, weight in scores_weights:
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0
    
    def get_critical_metrics(self) -> List[Dict[str, Any]]:
        """Get metrics that need attention"""
        
        critical = []
        
        # Check KPIs
        for agent in self.oag.get_agents().values():
            for kpi in agent.kpis:
                attainment = self.calculate_kpi_attainment(kpi)
                if attainment < 50:
                    critical.append({
                        "type": "kpi",
                        "id": kpi.id,
                        "metric": kpi.metric,
                        "current": self.kpi_values.get(kpi.id, kpi.current),
                        "target": kpi.target,
                        "attainment": attainment,
                        "owner": agent.role
                    })
            
            # Check OKRs
            for okr in agent.okrs:
                attainment = self.calculate_okr_attainment(okr)
                if attainment < 50:
                    critical.append({
                        "type": "okr",
                        "id": okr.objective.id,
                        "objective": okr.objective.title,
                        "attainment": attainment,
                        "owner": agent.role
                    })
        
        return critical
    
    def calculate_all(self) -> Dict[str, Any]:
        """Calculate all metrics"""
        
        return {
            "rollups": self.calculate_rollups(),
            "health": self.calculate_health_score(),
            "critical": self.get_critical_metrics()
        }
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current state of all metrics"""
        
        metrics = {
            "okrs": {},
            "kpis": {},
            "tasks": {}
        }
        
        # Collect OKR states
        for agent in self.oag.get_agents().values():
            for okr in agent.okrs:
                metrics["okrs"][okr.objective.id] = {
                    "title": okr.objective.title,
                    "owner": agent.role,
                    "attainment": self.calculate_okr_attainment(okr),
                    "key_results": [
                        {
                            "id": kr.id,
                            "metric": kr.metric,
                            "current": self.kr_values.get(kr.id, kr.current),
                            "target": kr.target
                        }
                        for kr in okr.key_results
                    ]
                }
            
            # Collect KPI states
            for kpi in agent.kpis:
                metrics["kpis"][kpi.id] = {
                    "metric": kpi.metric,
                    "owner": agent.role,
                    "current": self.kpi_values.get(kpi.id, kpi.current),
                    "target": kpi.target,
                    "attainment": self.calculate_kpi_attainment(kpi)
                }
        
        # Collect task states
        for task_id, task in self.oag.get_tasks().items():
            metrics["tasks"][task_id] = {
                "description": task.description,
                "status": task.status.value,
                "cost": task.cost.actual_cost_usd
            }
        
        return metrics