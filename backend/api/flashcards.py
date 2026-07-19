from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys
import hashlib
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from flashcards.flashcard_generator import FlashcardGenerator

router = APIRouter()

# Global flashcard generator instance (lazy loaded)
flashcard_generator = None

# Simple in-memory cache
flashcard_cache = {}

def get_flashcard_generator():
    global flashcard_generator
    if flashcard_generator is None:
        flashcard_generator = FlashcardGenerator()
    return flashcard_generator

def cache_key(text: str, num_cards: int) -> str:
    """Generate cache key from text and parameters."""
    return hashlib.md5(f"{text}_{num_cards}".encode()).hexdigest()

class FlashcardsRequest(BaseModel):
    text: str
    num_cards: int = 10

@router.post("/generate")
async def generate_flashcards(request: FlashcardsRequest):
    """
    Generate flashcards from text.
    """
    # Check cache first
    key = cache_key(request.text, request.num_cards)
    if key in flashcard_cache:
        return flashcard_cache[key]

    try:
        fg = get_flashcard_generator()
        flashcards = fg.generate_flashcards(
            request.text,
            num_cards=request.num_cards
        )
        result = {"flashcards": flashcards}
        # Cache the result
        flashcard_cache[key] = result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flashcard generation failed: {str(e)}")
