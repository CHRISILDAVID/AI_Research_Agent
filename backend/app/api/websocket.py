"""WebSocket endpoint for real-time research streaming.

Provides a live connection for the frontend to receive agent status
updates, tool call notifications, and the final report as they happen.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.graph import run_research

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Active WebSocket connections
# ---------------------------------------------------------------------------
_active_connections: dict[str, WebSocket] = {}


async def _send_event(ws: WebSocket, event: str, data: dict) -> None:
    """Send a JSON event through the WebSocket."""
    try:
        await ws.send_json({
            "event": event,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        })
    except Exception:
        logger.warning("Failed to send WebSocket event: %s", event)


@router.websocket("/ws/research/{session_id}")
async def research_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for streaming research progress.

    The client connects with a session_id and sends a start message
    with the research topic.  The server streams back events as the
    multi-agent pipeline executes.

    Client → Server Messages::

        {"action": "start", "topic": "...", "depth": "standard"}

    Server → Client Events::

        {"event": "status", "data": {"status": "connected"}}
        {"event": "agent_start", "data": {"agent": "supervisor"}}
        {"event": "tool_call", "data": {"tool": "web_search", "args": {...}}}
        {"event": "agent_step", "data": {"node": "researcher", ...}}
        {"event": "report", "data": {"content": "# Report..."}}
        {"event": "complete", "data": {"session_id": "..."}}
        {"event": "error", "data": {"message": "..."}}
    """
    await websocket.accept()
    _active_connections[session_id] = websocket
    logger.info("WebSocket connected for session %s", session_id)

    try:
        await _send_event(websocket, "status", {
            "status": "connected",
            "session_id": session_id,
        })

        # Wait for the start command from the client
        raw_message = await websocket.receive_text()
        message = json.loads(raw_message)

        if message.get("action") != "start":
            await _send_event(websocket, "error", {
                "message": "Expected 'start' action",
            })
            return

        topic = message.get("topic", "")
        depth = message.get("depth", "standard")

        if not topic:
            await _send_event(websocket, "error", {
                "message": "Research topic is required",
            })
            return

        await _send_event(websocket, "status", {
            "status": "starting",
            "topic": topic,
            "depth": depth,
        })

        # Define the streaming callback
        async def stream_callback(event_type: str, data: dict) -> None:
            """Forward agent events to the WebSocket client."""
            await _send_event(websocket, event_type, data)

        # Run the research pipeline with streaming
        final_state = await run_research(
            topic=topic,
            session_id=session_id,
            depth=depth,
            callback=stream_callback,
        )

        # Send the final report
        report = final_state.get("report", "")
        sources = final_state.get("sources", [])

        await _send_event(websocket, "report", {
            "content": report,
            "sources_count": len(sources),
            "chunks_stored": final_state.get("chunks_stored", 0),
        })

        await _send_event(websocket, "complete", {
            "session_id": session_id,
            "status": "completed",
        })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for session %s", session_id)
    except json.JSONDecodeError:
        await _send_event(websocket, "error", {
            "message": "Invalid JSON message",
        })
    except Exception as e:
        logger.exception("WebSocket error for session %s: %s", session_id, e)
        try:
            await _send_event(websocket, "error", {
                "message": str(e),
            })
        except Exception:
            pass
    finally:
        _active_connections.pop(session_id, None)
        logger.info("WebSocket cleanup for session %s", session_id)
