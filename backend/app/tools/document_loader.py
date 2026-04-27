"""Document loader tool for processing uploaded PDFs and text files.

Handles PDF parsing, text extraction, chunking, and indexing into
the session's ChromaDB vector store.
"""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.tools import tool

from app.config import UPLOAD_DIR
from app.rag.chunker import chunk_documents

logger = logging.getLogger(__name__)


@tool
def load_document(filename: str, session_id: str = "") -> str:
    """Load and index a document (PDF or text) into the research knowledge base.

    The document is read from the uploads directory, chunked, and stored
    in the session's vector store for later retrieval.

    Args:
        filename: Name of the file in the uploads directory.
        session_id: Research session ID for vector store indexing.

    Returns:
        A summary of how many chunks were extracted and indexed.
    """
    from app.rag.vectorstore import add_documents

    filepath = UPLOAD_DIR / filename
    if not filepath.exists():
        return f"Error: File '{filename}' not found in uploads directory."

    try:
        documents: list[Document] = []
        suffix = filepath.suffix.lower()

        if suffix == ".pdf":
            documents = _load_pdf(filepath)
        elif suffix in {".txt", ".md", ".rst"}:
            documents = _load_text(filepath)
        else:
            return f"Unsupported file format: {suffix}. Supported: .pdf, .txt, .md"

        if not documents:
            return f"No content could be extracted from '{filename}'."

        # Chunk the documents
        chunks = chunk_documents(documents)

        # Add metadata
        for chunk in chunks:
            chunk.metadata.update({
                "source": filename,
                "type": "uploaded_document",
            })

        # Store in vector DB
        if chunks and session_id:
            added = add_documents(session_id, chunks)
            logger.info(
                "Indexed %d chunks from '%s' into session %s",
                added, filename, session_id,
            )
            return (
                f"Successfully loaded '{filename}': extracted {len(documents)} pages, "
                f"created {added} searchable chunks."
            )

        return f"Loaded '{filename}' but no session ID provided for indexing."

    except Exception as e:
        logger.exception("Failed to load document: %s", filename)
        return f"Error loading '{filename}': {e!s}"


def _load_pdf(filepath: Path) -> list[Document]:
    """Extract text from a PDF file using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(str(filepath))
    documents = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            documents.append(
                Document(
                    page_content=text,
                    metadata={"page": i + 1, "source": filepath.name},
                )
            )

    return documents


def _load_text(filepath: Path) -> list[Document]:
    """Load a plain text / markdown file."""
    content = filepath.read_text(encoding="utf-8", errors="replace")
    if not content.strip():
        return []

    return [
        Document(
            page_content=content,
            metadata={"source": filepath.name},
        )
    ]
