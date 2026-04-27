"""Supervisor agent node.

The supervisor is the orchestrator of the research pipeline.  It
analyses the current state of the research and decides which agent
to invoke next — or whether the pipeline is complete.
"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agents.state import AgentState
from app.config import GEMINI_MODEL, GOOGLE_API_KEY

logger = logging.getLogger(__name__)

SUPERVISOR_SYSTEM_PROMPT = """\
You are the Supervisor Agent in a multi-agent research system. Your role is
to orchestrate the research pipeline by deciding which agent to invoke next.

## Available Agents
- **researcher**: Searches the web, loads documents, and gathers information
  into the knowledge base. Use when more information is needed.
- **writer**: Synthesizes the gathered research into a structured report.
  Use when sufficient research has been collected.
- **FINISH**: The research is complete and the report has been generated.

## Decision Rules
1. If no research has been done yet → route to "researcher"
2. If the researcher has gathered sources but no report exists → route to "writer"
3. If the research depth is "deep" and fewer than 3 search rounds done → route to "researcher"
4. If a report has been generated → route to "FINISH"
5. If max iterations reached → route to "writer" (to wrap up)

## Current State
- Topic: {topic}
- Depth: {depth}
- Sources found: {sources_count}
- Chunks in knowledge base: {chunks_stored}
- Report exists: {has_report}
- Iteration: {iteration}/{max_iterations}

Respond with ONLY a JSON object: {{"next": "researcher" | "writer" | "FINISH"}}
"""


def supervisor_node(state: AgentState) -> dict:
    """Supervisor node — decides the next step in the research pipeline.

    Returns a partial state update with the routing decision appended
    as a message and ``current_agent`` set accordingly.
    """
    topic = state.get("research_topic", "")
    depth = state.get("research_depth", "standard")
    sources = state.get("sources", [])
    chunks_stored = state.get("chunks_stored", 0)
    report = state.get("report", "")
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 5)

    # Fast-path: if we already have a report, we're done
    if report:
        logger.info("Supervisor: Report exists, routing to FINISH")
        return {
            "current_agent": "FINISH",
            "iteration": iteration + 1,
        }

    # Fast-path: max iterations reached, force writer
    if iteration >= max_iterations:
        logger.info("Supervisor: Max iterations reached, forcing writer")
        return {
            "current_agent": "writer",
            "iteration": iteration + 1,
        }

    # Use LLM for nuanced routing decisions
    try:
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.0,
        )

        prompt = SUPERVISOR_SYSTEM_PROMPT.format(
            topic=topic,
            depth=depth,
            sources_count=len(sources),
            chunks_stored=chunks_stored,
            has_report=bool(report),
            iteration=iteration,
            max_iterations=max_iterations,
        )

        response = llm.invoke([
            SystemMessage(content=prompt),
            HumanMessage(content="Decide the next agent to invoke."),
        ])

        # Parse the routing decision
        content = response.content.strip()
        # Handle markdown code blocks in response
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        decision = json.loads(content)
        next_agent = decision.get("next", "researcher")

        logger.info("Supervisor routed to: %s (iteration %d)", next_agent, iteration)

        return {
            "current_agent": next_agent,
            "iteration": iteration + 1,
        }

    except Exception as e:
        logger.exception("Supervisor LLM call failed: %s", e)
        # Fallback: if no sources yet → research; else → write
        fallback = "researcher" if not sources else "writer"
        return {
            "current_agent": fallback,
            "iteration": iteration + 1,
        }
