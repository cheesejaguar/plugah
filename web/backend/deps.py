"""
Dependencies and utilities for FastAPI
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    app_name: str = "Plugah.ai"
    debug: bool = True
    max_budget: float = 10000.0
    default_budget_policy: str = "balanced"
    session_timeout_minutes: int = 60
    openai_api_key: Optional[str] = None
    use_real_execution: bool = False
    default_llm_model: str = "gpt-3.5-turbo"
    cache_dir: str = ".cache"
    redis_url: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


# Session storage (in production, use Redis or database)
sessions: dict[str, dict] = {}


class SessionData(BaseModel):
    """Session data model"""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    state: str = "initialized"
    prompt: Optional[str] = None
    budget: Optional[float] = None
    prd: Optional[dict] = None
    oag: Optional[dict] = None
    boardroom: Optional[Any] = None


def get_session(session_id: str) -> Optional[SessionData]:
    """Get session by ID"""
    return sessions.get(session_id)


def create_session() -> SessionData:
    """Create new session"""
    session = SessionData()
    sessions[session.session_id] = session
    return session


def update_session(session_id: str, **kwargs) -> Optional[SessionData]:
    """Update session data"""
    session = sessions.get(session_id)
    if session:
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        session.updated_at = datetime.utcnow()
    return session


def delete_session(session_id: str) -> bool:
    """Delete session"""
    if session_id in sessions:
        del sessions[session_id]
        return True
    return False
