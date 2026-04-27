"""Research agent node.

The researcher gathers information by searching the web and querying
uploaded documents. All findings are stored in the ChromaDB vector
store for later synthesis by the writer agent.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agents.state import AgentState
from app.config import GEMINI_MODEL, GOOGLE_API_KEY
from app.tools.rag_query import rag_query
from app.tools.web_search import web_search

logger = logging.getLogger(__name__)

RESEARCHER_SYSTEM_PROMPT = """\
You are the Research Agent in a multi-agent research system. Your job is
to gather comprehensive information about the given topic.

## Your Tools
- **web_search(query, session_id)**: Search the web. Results are automatically
  indexed into the knowledge base. Craft specific, targeted queries.
- **rag_query(query, session_id)**: Search the existing knowledge base for
  previously gathered information.

## Instructions
1. Start by searching for the main topic with a broad query.
2. Based on initial results, formulate 2-3 more specific follow-up queries
   to fill knowledge gaps.
3. Focus on finding factual, well-sourced information.
4. After gathering sufficient information, summarize what you've found.

## Topic: {topic}
## Research Depth: {depth}
## Session ID: {session_id}

Execute your research now. Use your tools to gather information, then
provide a summary of what you've discovered.
"""


def researcher_node(state: AgentState) -> dict:
    """Research agent node — gathers information using web search and RAG.

    The researcher uses tool-calling to autonomously search the web
    and index findings into the vector store.
    """
    topic = state.get("research_topic", "")
    depth = state.get("research_depth", "standard")
    session_id = state.get("session_id", "")
    sources = state.get("sources", [])
    chunks_stored = state.get("chunks_stored", 0)

    # Determine number of search queries based on depth
    search_rounds = {"quick": 1, "standard": 2, "deep": 3}.get(depth, 2)

    try:
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3,
        )

        # Bind tools to the LLM
        tools = [web_search, rag_query]
        llm_with_tools = llm.bind_tools(tools)

        prompt = RESEARCHER_SYSTEM_PROMPT.format(
            topic=topic,
            depth=depth,
            session_id=session_id,
        )

        messages = [
            SystemMessage(content=prompt),
            HumanMessage(
                content=(
                    f"Research the topic: '{topic}'. "
                    f"Perform {search_rounds} rounds of web searches with different "
                    f"query angles. Session ID for all tool calls: '{session_id}'"
                )
            ),
        ]

        # Iterative tool-calling loop
        new_sources: list[dict] = []
        total_new_chunks = 0

        for round_num in range(search_rounds + 1):  # +1 for potential follow-ups
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            # Check for tool calls
            if not response.tool_calls:
                break  # No more tools to call, agent is done

            # Execute tool calls
            from langchain_core.messages import ToolMessage

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # Inject session_id into tool args
                tool_args["session_id"] = session_id

                logger.info(
                    "Researcher calling tool: %s(%s)",
                    tool_name,
                    {k: v[:50] if isinstance(v, str) else v for k, v in tool_args.items()},
                )

                # Execute the tool
                if tool_name == "web_search":
                    result = web_search.invoke(tool_args)
                    # Track sources
                    new_sources.append({
                        "query": tool_args.get("query", ""),
                        "type": "web_search",
                    })
                    total_new_chunks += 5  # Approximate
                elif tool_name == "rag_query":
                    result = rag_query.invoke(tool_args)
                else:
                    result = f"Unknown tool: {tool_name}"

                messages.append(
                    ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                )

        # Extract the final summary from the last AI message
        summary = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                summary = msg.content
                break

        logger.info(
            "Researcher completed: %d new sources, ~%d new chunks",
            len(new_sources),
            total_new_chunks,
        )

        return {
            "messages": [AIMessage(content=f"[Researcher] {summary}")],
            "sources": sources + new_sources,
            "chunks_stored": chunks_stored + total_new_chunks,
            "current_agent": "supervisor",
        }

    except Exception as e:
        logger.exception("Research agent failed: %s", e)
        return {
            "messages": [AIMessage(content=f"[Researcher] Error during research: {e!s}")],
            "current_agent": "supervisor",
        }
