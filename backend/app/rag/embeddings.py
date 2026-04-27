"""Embedding provider for the RAG pipeline.

Wraps the Google Gemini embedding model behind a thin interface so the
rest of the codebase never imports provider-specific classes directly.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import GEMINI_EMBEDDING_MODEL, GOOGLE_API_KEY


@lru_cache(maxsize=1)
def get_embedding_model() -> GoogleGenerativeAIEmbeddings:
    """Return a singleton Gemini embedding model instance.

    The result is cached so repeated calls reuse the same object,
    avoiding redundant HTTP client creation.
    """
    return GoogleGenerativeAIEmbeddings(
        model=GEMINI_EMBEDDING_MODEL,
        google_api_key=GOOGLE_API_KEY,
    )
