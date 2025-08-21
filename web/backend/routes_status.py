"""
Status and monitoring routes
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import networkx as nx

from .deps import get_session

router = APIRouter()


@router.get("/oag/{session_id}")
async def get_oag(session_id: str):
    """Get current OAG for a session"""
    
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.oag:
        raise HTTPException(status_code=400, detail="OAG not generated yet")
    
    return {
        "session_id": session_id,
        "oag": session.oag
    }


@router.get("/summary/{session_id}")
async def get_summary(session_id: str):
    """Get execution summary"""
    
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.boardroom:
        raise HTTPException(status_code=400, detail="Session not initialized")
    
    status = session.boardroom.get_status()
    
    return {
        "session_id": session_id,
        "phase": status.get("phase"),
        "budget": status.get("budget"),
        "metrics": status.get("metrics"),
        "execution_progress": status.get("execution_progress")
    }


@router.get("/orgchart/{session_id}")
async def get_orgchart(session_id: str):
    """Get organization chart data for visualization"""
    
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.oag:
        raise HTTPException(status_code=400, detail="OAG not generated yet")
    
    # Build org chart structure
    org_chart = build_org_chart(session.oag)
    
    return {
        "session_id": session_id,
        "chart": org_chart
    }


def build_org_chart(oag: Dict[str, Any]) -> Dict[str, Any]:
    """Build organization chart structure for frontend"""
    
    nodes = oag.get("nodes", {})
    
    # Group agents by level
    by_level = {
        "C_SUITE": [],
        "VP": [],
        "DIRECTOR": [],
        "MANAGER": [],
        "IC": []
    }
    
    # Build hierarchy
    for node_id, node in nodes.items():
        if node.get("node_type") == "agent":
            level = node.get("level", "IC")
            agent_info = {
                "id": node_id,
                "role": node.get("role"),
                "specialization": node.get("specialization"),
                "manager_id": node.get("manager_id"),
                "tools": len(node.get("tools", [])),
                "okrs": len(node.get("okrs", [])),
                "kpis": len(node.get("kpis", []))
            }
            by_level[level].append(agent_info)
    
    # Build tree structure
    tree = {
        "id": "root",
        "name": "Organization",
        "children": []
    }
    
    # Add Board Room
    board_room = {
        "id": "board_room",
        "name": "Board Room",
        "children": [
            {
                "id": agent["id"],
                "name": agent["role"],
                "data": agent
            }
            for agent in by_level["C_SUITE"]
        ]
    }
    tree["children"].append(board_room)
    
    # Add departments
    if by_level["VP"]:
        departments = {
            "id": "departments",
            "name": "Departments",
            "children": []
        }
        
        for vp in by_level["VP"]:
            dept = {
                "id": f"dept_{vp['id']}",
                "name": vp["role"],
                "data": vp,
                "children": []
            }
            
            # Add directors under this VP
            for director in by_level["DIRECTOR"]:
                if director["manager_id"] == vp["id"]:
                    dir_node = {
                        "id": director["id"],
                        "name": director["role"],
                        "data": director,
                        "children": []
                    }
                    
                    # Add managers under this director
                    for manager in by_level["MANAGER"]:
                        if manager["manager_id"] == director["id"]:
                            mgr_node = {
                                "id": manager["id"],
                                "name": manager["role"],
                                "data": manager,
                                "children": []
                            }
                            
                            # Add ICs under this manager
                            for ic in by_level["IC"]:
                                if ic["manager_id"] == manager["id"]:
                                    ic_node = {
                                        "id": ic["id"],
                                        "name": ic["specialization"] or ic["role"],
                                        "data": ic
                                    }
                                    mgr_node["children"].append(ic_node)
                            
                            dir_node["children"].append(mgr_node)
                    
                    dept["children"].append(dir_node)
            
            departments["children"].append(dept)
        
        tree["children"].append(departments)
    
    # Add task summary
    tasks = [n for n in nodes.values() if n.get("node_type") == "task"]
    task_summary = {
        "total": len(tasks),
        "by_status": {}
    }
    
    for task in tasks:
        status = task.get("status", "planned")
        task_summary["by_status"][status] = task_summary["by_status"].get(status, 0) + 1
    
    return {
        "tree": tree,
        "agents_count": len([n for n in nodes.values() if n.get("node_type") == "agent"]),
        "tasks": task_summary
    }


@router.get("/metrics/{session_id}")
async def get_metrics(session_id: str):
    """Get current metrics and KPIs"""
    
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.boardroom:
        raise HTTPException(status_code=400, detail="Session not initialized")
    
    if hasattr(session.boardroom, 'metrics_engine') and session.boardroom.metrics_engine:
        metrics = session.boardroom.metrics_engine.calculate_all()
        return {
            "session_id": session_id,
            "metrics": metrics
        }
    else:
        return {
            "session_id": session_id,
            "metrics": {
                "rollups": {},
                "health": {},
                "critical": []
            }
        }


@router.get("/artifacts/{session_id}")
async def list_artifacts(session_id: str):
    """List artifacts for a session"""
    
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.boardroom:
        raise HTTPException(status_code=400, detail="Session not initialized")
    
    # Get artifacts from audit logger
    artifacts = []
    if hasattr(session.boardroom, 'audit_logger'):
        artifacts = session.boardroom.audit_logger._list_artifacts()
    
    return {
        "session_id": session_id,
        "artifacts": artifacts
    }