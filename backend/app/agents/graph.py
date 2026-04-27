"""LangGraph graph definition — the research pipeline orchestrator.

Builds a ``StateGraph`` with three nodes (supervisor, researcher, writer)
connected by conditional edges.  The supervisor decides routing at each
step, creating an autonomous loop that researches and writes until done.

Flow::

    START → supervisor → researcher → supervisor → writer → supervisor → END
                  ↑______________|           ↑_____________|
"""

from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from app.agents.researcher import researcher_node
from app.agents.state import AgentState
from app.agents.supervisor import supervisor_node
from app.agents.writer import writer_node
from app.config import MAX_RESEARCH_ITERATIONS

logger = logging.getLogger(__name__)


def _route_supervisor(state: AgentState) -> str:
    """Conditional edge function — reads ``current_agent`` from state
    and routes to the appropriate node (or END)."""
    next_agent = state.get("current_agent", "researcher")

    if next_agent == "FINISH":
        return END
    if next_agent in {"researcher", "writer"}:
        return next_agent

    # Safety fallback
    logger.warning("Unknown routing target: %s, defaulting to researcher", next_agent)
    return "researcher"


def build_research_graph() -> StateGraph:
    """Construct and compile the multi-agent research graph.

    Returns
    -------
    StateGraph
        Compiled LangGraph ready for ``.invoke()`` or ``.stream()``.
    """
    graph = StateGraph(AgentState)

    # --- Add nodes ---
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("writer", writer_node)

    # --- Set entry point ---
    graph.set_entry_point("supervisor")

    # --- Add edges ---
    # Supervisor routes conditionally to researcher, writer, or END
    graph.add_conditional_edges(
        "supervisor",
        _route_supervisor,
        {
            "researcher": "researcher",
            "writer": "writer",
            END: END,
        },
    )

    # Researcher and Writer always return to supervisor for the next decision
    graph.add_edge("researcher", "supervisor")
    graph.add_edge("writer", "supervisor")

    compiled = graph.compile()
    logger.info("Research graph compiled successfully")
    return compiled


def create_initial_state(
    topic: str,
    session_id: str,
    depth: str = "standard",
) -> AgentState:
    """Create the initial state dict for a new research session.

    Parameters
    ----------
    topic:
        The user's research query.
    session_id:
        Unique session identifier.
    depth:
        ``"quick"`` | ``"standard"`` | ``"deep"``.
    """
    max_iters = {
        "quick": 3,
        "standard": MAX_RESEARCH_ITERATIONS,
        "deep": MAX_RESEARCH_ITERATIONS + 3,
    }.get(depth, MAX_RESEARCH_ITERATIONS)

    return AgentState(
        messages=[],
        research_topic=topic,
        research_depth=depth,
        sources=[],
        chunks_stored=0,
        report="",
        current_agent="",
        iteration=0,
        max_iterations=max_iters,
        session_id=session_id,
    )


async def run_research(
    topic: str,
    session_id: str,
    depth: str = "standard",
    callback=None,
) -> AgentState:
    """Run the full research pipeline asynchronously.

    Parameters
    ----------
    topic:
        Research query.
    session_id:
        Unique session identifier.
    depth:
        Research depth level.
    callback:
        Optional async callable invoked with ``(event_type, data)``
        at each graph step for real-time streaming.

    Returns
    -------
    AgentState
        Final state containing the report, sources, etc.
    """
    graph = build_research_graph()
    initial_state = create_initial_state(topic, session_id, depth)

    logger.info("Starting research pipeline for topic='%s', session=%s", topic, session_id)

    # Stream through graph steps for real-time updates
    final_state = initial_state
    async for event in graph.astream(initial_state):
        for node_name, node_output in event.items():
            logger.info("Graph step: node=%s", node_name)

            if callback:
                await callback(
                    "agent_step",
                    {
                        "node": node_name,
                        "current_agent": node_output.get("current_agent", ""),
                        "chunks_stored": node_output.get("chunks_stored", 0),
                        "sources_count": len(node_output.get("sources", [])),
                        "has_report": bool(node_output.get("report")),
                    },
                )

            # Merge output into final state
            for key, value in node_output.items():
                if key == "messages":
                    final_state["messages"] = final_state.get("messages", []) + value
                else:
                    final_state[key] = value

    logger.info(
        "Research pipeline completed: %d sources, report=%s",
        len(final_state.get("sources", [])),
        bool(final_state.get("report")),
    )

    return final_state
