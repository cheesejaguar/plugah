"""
Startup phase routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio

from plugah.boardroom import BoardRoom, Startup
from .deps import create_session, get_session, update_session

router = APIRouter()


class StartupRequest(BaseModel):
    """Startup request model"""
    
    project_title: str = Field(..., description="Project title")
    prompt: str = Field(..., description="Project description/prompt")
    budget_usd: float = Field(..., gt=0, le=10000, description="Budget in USD")
    domain: Optional[str] = Field(None, description="Project domain")


class StartupResponse(BaseModel):
    """Startup response model"""
    
    session_id: str
    questions: List[str]
    project_title: str
    budget: float


class AnswersRequest(BaseModel):
    """Discovery answers request"""
    
    session_id: str
    answers: List[str]


class PRDResponse(BaseModel):
    """PRD response model"""
    
    session_id: str
    prd: Dict[str, Any]


@router.post("/begin", response_model=StartupResponse)
async def begin_startup(request: StartupRequest):
    """Begin startup discovery phase"""
    
    # Create session
    session = create_session()
    
    # Initialize board room
    boardroom = BoardRoom(project_id=session.session_id)
    
    # Store in session
    update_session(
        session.session_id,
        prompt=request.prompt,
        budget=request.budget_usd,
        boardroom=boardroom,
        state="discovery"
    )
    
    # Run startup phase
    try:
        discovery = await boardroom.startup_phase(
            request.prompt,
            request.budget_usd,
            {"domain": request.domain} if request.domain else None
        )
        
        return StartupResponse(
            session_id=session.session_id,
            questions=discovery["questions"],
            project_title=request.project_title,
            budget=request.budget_usd
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/questions")
async def get_questions(session_id: str):
    """Get discovery questions for a session"""
    
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not hasattr(session, 'boardroom') or not session.boardroom:
        raise HTTPException(status_code=400, detail="Session not initialized")
    
    # Get questions from boardroom
    if session.boardroom.startup.discovery_questions:
        return {
            "session_id": session_id,
            "questions": session.boardroom.startup.discovery_questions
        }
    else:
        raise HTTPException(status_code=400, detail="No questions generated yet")


@router.post("/answers", response_model=PRDResponse)
async def submit_answers(request: AnswersRequest):
    """Submit discovery answers and generate PRD"""
    
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.boardroom:
        raise HTTPException(status_code=400, detail="Session not initialized")
    
    try:
        # Process answers
        prd = await session.boardroom.process_discovery(
            request.answers,
            session.prompt,
            session.budget
        )
        
        # Update session
        update_session(
            request.session_id,
            prd=prd,
            state="planning"
        )
        
        return PRDResponse(
            session_id=request.session_id,
            prd=prd
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prd/{session_id}")
async def get_prd(session_id: str):
    """Get PRD for a session"""
    
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.prd:
        raise HTTPException(status_code=400, detail="PRD not generated yet")
    
    return {
        "session_id": session_id,
        "prd": session.prd
    }