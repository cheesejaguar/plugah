"""
FastAPI backend for plugah.ai demo
"""

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

try:
    from .routes_run import router as run_router
    from .routes_startup import router as startup_router
    from .routes_status import router as status_router
except ImportError:
    from routes_run import router as run_router
    from routes_startup import router as startup_router
    from routes_status import router as status_router

app = FastAPI(
    title="Plugah.ai API",
    description="Multi-agent orchestration system",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(startup_router, prefix="/startup", tags=["startup"])
app.include_router(run_router, prefix="/run", tags=["execution"])
app.include_router(status_router, prefix="/status", tags=["status"])

# Serve static files if they exist
static_path = Path(__file__).parent.parent / "frontend" / "dist"
if static_path.exists():
    # Mount UI under /app to avoid shadowing API routes like /health
    app.mount("/app", StaticFiles(directory=str(static_path), html=True), name="static")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "plugah-api"}


@app.get("/api/info")
async def api_info():
    """API information"""
    return {
        "name": "Plugah.ai",
        "version": "0.1.0",
        "description": "Multi-agent orchestration with organizational hierarchy"
    }


if __name__ == "__main__":
    uvicorn.run(
        "web.backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
