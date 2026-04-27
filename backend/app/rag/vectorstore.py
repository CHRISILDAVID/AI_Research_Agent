"""ChromaDB vector store manager.

Provides per-session collections so each research query gets its own
isolated namespace.  Collections persist to disk in ``CHROMA_PERSIST_DIR``
and are automatically created on first access.
"""

from __future__ import annotations

import logging

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import CHROMA_PERSIST_DIR, RAG_TOP_K
from app.rag.embeddings import get_embedding_model

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Persistent ChromaDB client (singleton at module level)
# ---------------------------------------------------------------------------
_chroma_client: chromadb.ClientAPI | None = None


def _get_client() -> chromadb.ClientAPI:
    """Lazily create / return the persistent ChromaDB client."""
    global _chroma_client  # noqa: PLW0603
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        logger.info("ChromaDB persistent client initialized at %s", CHROMA_PERSIST_DIR)
    return _chroma_client


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_vectorstore(session_id: str) -> Chroma:
    """Return a LangChain ``Chroma`` wrapper for the given session's collection.

    Parameters
    ----------
    session_id:
        Research session identifier used as the collection name.
    """
    return Chroma(
        client=_get_client(),
        collection_name=f"research_{session_id}",
        embedding_function=get_embedding_model(),
    )


def add_documents(
    session_id: str,
    documents: list[Document],
) -> int:
    """Chunk-safe addition of documents to the session's vector store.

    Returns the number of documents actually added.
    """
    if not documents:
        return 0

    store = get_vectorstore(session_id)
    store.add_documents(documents)
    logger.info(
        "Added %d documents to collection research_%s",
        len(documents),
        session_id,
    )
    return len(documents)


def similarity_search(
    session_id: str,
    query: str,
    top_k: int | None = None,
) -> list[Document]:
    """Run a semantic similarity search against the session's vector store.

    Parameters
    ----------
    session_id:
        Research session identifier.
    query:
        Natural-language query to embed and search for.
    top_k:
        Number of results to return.  Defaults to ``RAG_TOP_K`` from config.

    Returns
    -------
    list[Document]
        Top-K most relevant documents, each with ``page_content`` and
        ``metadata`` (source URL, title, etc.).
    """
    k = top_k or RAG_TOP_K
    store = get_vectorstore(session_id)

    try:
        results = store.similarity_search(query, k=k)
        logger.info(
            "RAG query returned %d results for session %s",
            len(results),
            session_id,
        )
        return results
    except Exception:
        logger.exception("Similarity search failed for session %s", session_id)
        return []


def delete_collection(session_id: str) -> None:
    """Remove a session's collection from ChromaDB."""
    try:
        client = _get_client()
        client.delete_collection(f"research_{session_id}")
        logger.info("Deleted collection research_%s", session_id)
    except Exception:
        logger.warning("Could not delete collection research_%s", session_id)


def list_collections() -> list[str]:
    """Return names of all research collections."""
    client = _get_client()
    return [c.name for c in client.list_collections()]
