"""FastAPI application entry point.

Starts the backend server with CORS middleware, mounts API routes
and WebSocket endpoints, and manages application lifecycle.
"""

from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.websocket import router as ws_router
from app.config import BACKEND_HOST, BACKEND_PORT, CORS_ORIGINS

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-30s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI Research Agent",
    description=(
        "An agentic AI system that autonomously researches topics using "
        "LangGraph multi-agent orchestration, RAG pipelines, and web search."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Mount Routers
# ---------------------------------------------------------------------------
app.include_router(api_router, prefix="/api")
app.include_router(ws_router)


# ---------------------------------------------------------------------------
# Lifecycle Events
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event() -> None:
    """Run on application startup."""
    logger.info("=" * 60)
    logger.info("  AI Research Agent — Backend Starting")
    logger.info("=" * 60)
    logger.info("CORS origins: %s", CORS_ORIGINS)
    logger.info("Docs available at: http://%s:%d/docs", BACKEND_HOST, BACKEND_PORT)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Run on application shutdown."""
    logger.info("AI Research Agent — Backend shutting down")


# ---------------------------------------------------------------------------
# Health Check (root)
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    """Root endpoint — basic service info."""
    return {
        "service": "AI Research Agent",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


# ---------------------------------------------------------------------------
# Run with Uvicorn
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        reload=True,
        log_level="info",
    )
