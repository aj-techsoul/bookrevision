from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys
import hashlib
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from simplifier.simplifier import Simplifier

router = APIRouter()

# Global simplifier instance (lazy loaded)
simplifier = None

# Simple in-memory cache
simplify_cache = {}

def get_simplifier():
    global simplifier
    if simplifier is None:
        simplifier = Simplifier()
    return simplifier

def cache_key(text: str, level: str) -> str:
    """Generate cache key from text and level."""
    return hashlib.md5(f"{text}_{level}".encode()).hexdigest()

class SimplifyRequest(BaseModel):
    text: str
    level: str = "high_school"

class ELI10Request(BaseModel):
    text: str

class WordSimplifyRequest(BaseModel):
    word: str

@router.post("/simplify")
async def simplify_text(request: SimplifyRequest):
    """
    Simplify text to a specified reading level.
    
    Levels: elementary, middle_school, high_school, college
    """
    # Check cache first
    key = cache_key(request.text, request.level)
    if key in simplify_cache:
        return simplify_cache[key]

    try:
        simp = get_simplifier()
        result = simp.simplify(request.text, request.level)
        # Cache the result
        simplify_cache[key] = result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simplification failed: {str(e)}")

@router.post("/eli10")
async def eli10(request: ELI10Request):
    """
    Explain Like I'm 10 - extreme simplification.
    """
    try:
        simp = get_simplifier()
        result = simp.eli10(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ELI10 failed: {str(e)}")

@router.post("/simplify-word")
async def simplify_word(request: WordSimplifyRequest):
    """
    Get simpler synonyms for a complex word.
    """
    try:
        simp = get_simplifier()
        result = simp.simplify_word(request.word)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Word simplification failed: {str(e)}")
