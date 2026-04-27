"""Text chunking utilities for the RAG pipeline.

Uses LangChain's ``RecursiveCharacterTextSplitter`` to split long texts
into semantically meaningful chunks while preserving metadata.
"""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import CHUNK_OVERLAP, CHUNK_SIZE


def get_splitter(
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> RecursiveCharacterTextSplitter:
    """Create a text splitter with configurable parameters."""
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or CHUNK_SIZE,
        chunk_overlap=chunk_overlap or CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def chunk_text(
    text: str,
    metadata: dict | None = None,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Document]:
    """Split a text string into LangChain ``Document`` chunks.

    Parameters
    ----------
    text:
        Raw text to split.
    metadata:
        Metadata dict attached to every resulting chunk.
    chunk_size:
        Maximum characters per chunk.
    chunk_overlap:
        Overlap between consecutive chunks.

    Returns
    -------
    list[Document]
        List of chunked documents, each carrying the supplied metadata.
    """
    if not text or not text.strip():
        return []

    splitter = get_splitter(chunk_size, chunk_overlap)
    docs = splitter.create_documents(
        texts=[text],
        metadatas=[metadata or {}],
    )
    return docs


def chunk_documents(
    documents: list[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Document]:
    """Split a list of Documents into smaller chunks, preserving metadata."""
    if not documents:
        return []

    splitter = get_splitter(chunk_size, chunk_overlap)
    return splitter.split_documents(documents)
