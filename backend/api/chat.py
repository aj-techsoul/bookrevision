from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from chatbot.rag_chatbot import RAGChatbot
from backend import shared_state

router = APIRouter()

# Chatbot singleton (lazy loaded)
_chatbot = None


def get_chatbot() -> RAGChatbot:
    """Return (and lazily create) the chatbot using SHARED embedding model and vector DB."""
    global _chatbot
    if _chatbot is None:
        emb_model = shared_state.get_embedding_model()
        vdb = shared_state.get_vector_db()
        _chatbot = RAGChatbot(emb_model, vdb)
    return _chatbot


class ChatRequest(BaseModel):
    question: str
    k: int = 4
    confidence_threshold: float = 0.25


@router.post("/chat")
async def chat_with_notes(request: ChatRequest):
    """
    Ask a question about uploaded documents using RAG.

    If no document is uploaded yet, the chatbot returns a helpful
    no-document message rather than crashing.
    """
    try:
        vdb = shared_state.get_vector_db()
        doc_count = len(shared_state.uploaded_documents)

        # If the vector DB is empty there is nothing to search
        if vdb.index.ntotal == 0:
            return {
                "answer": (
                    "📂 No document has been uploaded yet.\n\n"
                    "Please go to the **Upload** page, upload a PDF, DOCX, or TXT file, "
                    "and then come back here to ask questions about it."
                ),
                "sources": [],
                "confidence": 0.0,
                "found": False,
                "doc_count": 0,
            }

        bot = get_chatbot()
        result = bot.answer_question(
            request.question,
            k=request.k,
            confidence_threshold=request.confidence_threshold,
        )
        result["doc_count"] = doc_count
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/status")
async def chat_status():
    """Return information about loaded documents."""
    vdb = shared_state.get_vector_db()
    return {
        "documents_loaded": len(shared_state.uploaded_documents),
        "total_chunks": vdb.index.ntotal,
        "document_names": list(shared_state.uploaded_documents.values()),
    }
