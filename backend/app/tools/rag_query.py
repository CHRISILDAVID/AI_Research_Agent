"""RAG query tool for semantic retrieval from the vector store.

Allows agents to search the accumulated research knowledge base
and retrieve relevant context with full source attribution.
"""

from __future__ import annotations

import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def rag_query(query: str, session_id: str = "", top_k: int = 5) -> str:
    """Query the research knowledge base for relevant information.

    Performs semantic similarity search against the session's ChromaDB
    vector store and returns the most relevant chunks with source info.

    Args:
        query: Natural language query to search for.
        session_id: Research session ID.
        top_k: Number of results to return.

    Returns:
        Formatted string of relevant research findings with sources.
    """
    from app.rag.vectorstore import similarity_search

    if not session_id:
        return "Error: No session ID provided for RAG query."

    try:
        results = similarity_search(session_id, query, top_k=top_k)

        if not results:
            return f"No relevant information found in the knowledge base for: '{query}'"

        formatted_parts: list[str] = []
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get("source", "Unknown")
            title = doc.metadata.get("title", "")
            doc_type = doc.metadata.get("type", "unknown")
            content = doc.page_content[:600]

            header = f"[{i}] "
            if title:
                header += f"{title} "
            header += f"(Source: {source}, Type: {doc_type})"

            formatted_parts.append(f"{header}\n{content}\n")

        return (
            f"Found {len(results)} relevant chunks for '{query}':\n\n"
            + "\n---\n".join(formatted_parts)
        )

    except Exception as e:
        logger.exception("RAG query failed: %s", query)
        return f"RAG query failed: {e!s}"
