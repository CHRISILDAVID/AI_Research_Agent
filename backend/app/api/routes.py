"""REST API route handlers.

Endpoints for starting research sessions, retrieving results,
uploading documents, and managing sessions.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.agents.graph import run_research
from app.config import MAX_UPLOAD_SIZE_MB, UPLOAD_DIR
from app.models.schemas import (
    ResearchReport,
    ResearchRequest,
    ResearchSession,
    SessionStatus,
    SourceInfo,
)
from app.rag.vectorstore import delete_collection

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# In-memory session store (production would use Redis/DB)
# ---------------------------------------------------------------------------
_sessions: dict[str, ResearchSession] = {}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/health")
async def health_check():
    """Service health check."""
    return {"status": "healthy", "service": "ai-research-agent"}


@router.post("/research", response_model=ResearchSession)
async def start_research(request: ResearchRequest):
    """Start a new research session.

    Launches the multi-agent research pipeline asynchronously
    and returns the session object immediately.
    """
    session_id = uuid4().hex[:12]

    session = ResearchSession(
        session_id=session_id,
        topic=request.topic,
        status=SessionStatus.PENDING,
    )
    _sessions[session_id] = session

    # Launch research in background
    asyncio.create_task(_execute_research(session_id, request))

    logger.info("Research session created: %s for topic '%s'", session_id, request.topic)
    return session


async def _execute_research(session_id: str, request: ResearchRequest) -> None:
    """Background task to run the full research pipeline."""
    session = _sessions.get(session_id)
    if not session:
        return

    try:
        session.status = SessionStatus.RESEARCHING

        # Run the agent pipeline
        final_state = await run_research(
            topic=request.topic,
            session_id=session_id,
            depth=request.depth,
            callback=lambda event_type, data: _update_session(session_id, event_type, data),
        )

        # Extract results
        report_text = final_state.get("report", "")
        sources = final_state.get("sources", [])
        chunks_stored = final_state.get("chunks_stored", 0)

        session.report = ResearchReport(
            title=request.topic,
            summary=report_text[:500] if report_text else "",
            detailed_analysis=report_text,
            sources=[
                SourceInfo(
                    title=s.get("title", ""),
                    url=s.get("url", s.get("query", "")),
                    snippet=s.get("snippet", ""),
                )
                for s in sources
                if isinstance(s, dict)
            ],
        )
        session.sources_found = len(sources)
        session.chunks_stored = chunks_stored
        session.status = SessionStatus.COMPLETED

        logger.info("Research session %s completed successfully", session_id)

    except Exception as e:
        logger.exception("Research session %s failed: %s", session_id, e)
        session.status = SessionStatus.FAILED
        session.report = ResearchReport(
            title=request.topic,
            summary=f"Research failed: {e!s}",
        )


async def _update_session(session_id: str, event_type: str, data: dict) -> None:
    """Callback for updating session state during pipeline execution."""
    session = _sessions.get(session_id)
    if not session:
        return

    current_agent = data.get("current_agent", "")
    if current_agent == "researcher":
        session.status = SessionStatus.RESEARCHING
    elif current_agent == "writer":
        session.status = SessionStatus.WRITING

    session.chunks_stored = data.get("chunks_stored", session.chunks_stored)
    session.sources_found = data.get("sources_count", session.sources_found)


@router.get("/research/{session_id}", response_model=ResearchSession)
async def get_research(session_id: str):
    """Get the current state of a research session."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return session


@router.get("/sessions")
async def list_sessions():
    """List all research sessions."""
    return {
        "sessions": [
            {
                "session_id": s.session_id,
                "topic": s.topic,
                "status": s.status.value,
                "created_at": s.created_at.isoformat(),
            }
            for s in _sessions.values()
        ],
        "total": len(_sessions),
    }


@router.delete("/research/{session_id}")
async def delete_session(session_id: str):
    """Delete a research session and its vector store data."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    delete_collection(session_id)
    del _sessions[session_id]
    return {"message": f"Session '{session_id}' deleted"}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), session_id: str = ""):
    """Upload a PDF or text document for research.

    The file is saved to the uploads directory and can be loaded
    by the research agent via the document_loader tool.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Validate file type
    allowed_types = {".pdf", ".txt", ".md"}
    suffix = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {allowed_types}",
        )

    # Validate file size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f} MB). Max: {MAX_UPLOAD_SIZE_MB} MB",
        )

    # Save file
    filepath = UPLOAD_DIR / file.filename
    with open(filepath, "wb") as f:
        f.write(content)

    logger.info("Uploaded file: %s (%.2f MB)", file.filename, size_mb)

    # If a session is active, auto-load into vector store
    if session_id:
        from app.tools.document_loader import load_document
        result = load_document.invoke({"filename": file.filename, "session_id": session_id})
        return {
            "filename": file.filename,
            "size_mb": round(size_mb, 2),
            "indexed": True,
            "result": result,
        }

    return {
        "filename": file.filename,
        "size_mb": round(size_mb, 2),
        "indexed": False,
        "message": "File uploaded. Provide a session_id to auto-index.",
    }
