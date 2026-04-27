"""Web search tool using the Tavily API.

Tavily is purpose-built for AI agent web search — it returns clean,
pre-processed content rather than raw HTML, making it ideal for RAG
ingestion.
"""

from __future__ import annotations

import logging

from langchain_core.documents import Document
from langchain_core.tools import tool

from app.config import MAX_SEARCH_RESULTS, TAVILY_API_KEY
from app.rag.chunker import chunk_text

logger = logging.getLogger(__name__)


@tool
def web_search(query: str, session_id: str = "") -> str:
    """Search the web for information on a given query.

    Uses the Tavily API to retrieve relevant web pages. Results are
    automatically chunked and stored in the session's vector store
    for later RAG retrieval.

    Args:
        query: The search query string.
        session_id: Research session ID for vector store indexing.

    Returns:
        A formatted string of search results with titles, URLs, and
        content snippets.
    """
    from tavily import TavilyClient

    from app.rag.vectorstore import add_documents

    if not TAVILY_API_KEY:
        return "Error: TAVILY_API_KEY not configured. Please set it in your .env file."

    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = client.search(
            query=query,
            max_results=MAX_SEARCH_RESULTS,
            include_raw_content=False,
            search_depth="advanced",
        )

        results = response.get("results", [])
        if not results:
            return f"No results found for query: '{query}'"

        # Format results for the agent's consumption
        formatted_parts: list[str] = []
        all_chunks: list[Document] = []

        for i, result in enumerate(results, 1):
            title = result.get("title", "Untitled")
            url = result.get("url", "")
            content = result.get("content", "")
            score = result.get("score", 0.0)

            formatted_parts.append(
                f"[{i}] {title}\n"
                f"    URL: {url}\n"
                f"    Relevance: {score:.2f}\n"
                f"    Content: {content[:500]}...\n"
            )

            # Chunk and prepare for vector store indexing
            if content and session_id:
                chunks = chunk_text(
                    text=content,
                    metadata={
                        "source": url,
                        "title": title,
                        "type": "web_search",
                        "query": query,
                        "relevance_score": score,
                    },
                )
                all_chunks.extend(chunks)

        # Store in vector DB
        if all_chunks and session_id:
            added = add_documents(session_id, all_chunks)
            logger.info("Indexed %d chunks from web search into session %s", added, session_id)

        return (
            f"Found {len(results)} results for '{query}':\n\n"
            + "\n".join(formatted_parts)
        )

    except Exception as e:
        logger.exception("Web search failed for query: %s", query)
        return f"Web search failed: {e!s}"
