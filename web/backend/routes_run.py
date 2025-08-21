"""
Planning and execution routes with SSE streaming
"""

from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import Dict, Any, AsyncGenerator
import asyncio
import json

from .deps import get_session, update_session

router = APIRouter()


class PlanRequest(BaseModel):
    """Plan request model"""
    session_id: str


class ExecuteRequest(BaseModel):
    """Execute request model"""
    session_id: str
    parallel: bool = True


@router.post("/plan")
async def plan_organization(request: PlanRequest):
    """Plan the organizational structure"""
    
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.boardroom or not session.prd:
        raise HTTPException(status_code=400, detail="Session not ready for planning")
    
    try:
        # Plan organization
        oag = await session.boardroom.plan_organization(
            session.prd,
            session.budget
        )
        
        # Store OAG in session
        update_session(
            request.session_id,
            oag=oag.model_dump(),
            state="planned"
        )
        
        return {
            "session_id": request.session_id,
            "success": True,
            "num_agents": len(oag.get_agents()),
            "num_tasks": len(oag.get_tasks()),
            "forecast_cost": oag.budget.forecast_cost_usd
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def execution_event_generator(
    session_id: str,
    parallel: bool = True
) -> AsyncGenerator[str, None]:
    """Generate SSE events during execution"""
    
    session = get_session(session_id)
    if not session or not session.boardroom:
        yield json.dumps({"error": "Session not found"})
        return
    
    # Event queue for callbacks
    event_queue = asyncio.Queue()
    
    # Add callback to capture events
    async def event_callback(event, data):
        await event_queue.put({"event": event, "data": data})
    
    session.boardroom.add_callback(event_callback)
    
    # Start execution in background
    execution_task = asyncio.create_task(
        session.boardroom.execute()
    )
    
    # Stream events
    try:
        while not execution_task.done():
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(
                    event_queue.get(),
                    timeout=0.5
                )
                
                yield json.dumps(event)
                
            except asyncio.TimeoutError:
                # Send heartbeat
                yield json.dumps({"event": "heartbeat"})
        
        # Get final result
        result = await execution_task
        
        # Send completion event
        yield json.dumps({
            "event": "execution_complete",
            "data": {
                "total_cost": result.get("total_cost", 0),
                "budget_remaining": result.get("budget_remaining", 0),
                "tasks_completed": len(result.get("results", {}))
            }
        })
        
        # Update session
        update_session(
            session_id,
            state="completed"
        )
        
    except Exception as e:
        yield json.dumps({
            "event": "error",
            "data": {"message": str(e)}
        })


@router.post("/execute")
async def execute_plan(request: ExecuteRequest):
    """Start execution and return SSE stream endpoint"""
    
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.boardroom or not session.oag:
        raise HTTPException(status_code=400, detail="Session not ready for execution")
    
    # Update state
    update_session(request.session_id, state="executing")
    
    return {
        "session_id": request.session_id,
        "stream_url": f"/run/stream/{request.session_id}",
        "message": "Execution started, connect to stream for updates"
    }


@router.get("/stream/{session_id}")
async def execution_stream(session_id: str, request: Request):
    """SSE stream for execution events"""
    
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return EventSourceResponse(
        execution_event_generator(session_id),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/progress/{session_id}")
async def get_progress(session_id: str):
    """Get execution progress"""
    
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.boardroom:
        raise HTTPException(status_code=400, detail="Session not initialized")
    
    if hasattr(session.boardroom, 'executor') and session.boardroom.executor:
        progress = session.boardroom.executor.get_progress()
        return {
            "session_id": session_id,
            "progress": progress
        }
    else:
        return {
            "session_id": session_id,
            "progress": {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "in_progress": 0,
                "completion_rate": 0
            }
        }