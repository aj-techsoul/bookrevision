"""
Shared application state — single instances of heavy ML objects.

Both upload.py and chat.py import from here so they operate on
the SAME embedding model and vector database. This is critical:
without sharing, documents uploaded via /api/upload would not be
visible to /api/chat/chat.
"""

from models.embedding_model import EmbeddingModel, VectorDatabase

# These are module-level singletons. They are lazy-initialised on
# first access so the server starts quickly.
_embedding_model: EmbeddingModel | None = None
_vector_db: VectorDatabase | None = None

# Track uploaded documents (doc_id -> filename)
uploaded_documents: dict = {}


def get_embedding_model() -> EmbeddingModel:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model


def get_vector_db() -> VectorDatabase:
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorDatabase(dimension=384)
    return _vector_db


def reset_vector_db():
    """Reset the vector database (e.g. when re-uploading a document)."""
    global _vector_db
    _vector_db = VectorDatabase(dimension=384)
