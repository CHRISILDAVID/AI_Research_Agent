"""Agent state schema shared across all LangGraph nodes.

The ``AgentState`` TypedDict defines the data that flows through the graph.
Every node reads from and writes to this shared state object.
"""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """Shared state for the multi-agent research pipeline.

    Attributes
    ----------
    messages : list[BaseMessage]
        Full conversation / reasoning trace. Uses ``operator.add`` as the
        reducer so each node *appends* rather than overwrites.
    research_topic : str
        The user's original research query.
    research_depth : str
        Depth of research: ``"quick"`` | ``"standard"`` | ``"deep"``.
    sources : list[dict]
        Web sources discovered during research.
        Each dict has ``{title, url, content, score}``.
    chunks_stored : int
        Running count of chunks written to the vector store.
    report : str
        The final Markdown report produced by the Writer agent.
    current_agent : str
        Which agent is currently executing (for frontend status display).
    iteration : int
        Number of supervisor routing cycles completed.
    max_iterations : int
        Safety cap to prevent runaway loops.
    session_id : str
        Unique identifier for this research session.
    """

    messages: Annotated[list[BaseMessage], operator.add]
    research_topic: str
    research_depth: str
    sources: list[dict]
    chunks_stored: int
    report: str
    current_agent: str
    iteration: int
    max_iterations: int
    session_id: str
