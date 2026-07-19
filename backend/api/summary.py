from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import hashlib
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from summarizer.summarizer import Summarizer

router = APIRouter()

# Global summarizer instance (lazy loaded)
summarizer = None

# Simple in-memory cache
summary_cache = {}


def get_summarizer():
    global summarizer
    if summarizer is None:
        summarizer = Summarizer()
    return summarizer


def cache_key(text: str, level: str) -> str:
    """Generate cache key from text and level."""
    return hashlib.md5(f"{text}_{level}".encode()).hexdigest()


class SummaryRequest(BaseModel):
    text: str
    level: str = "150w"


@router.post("/summarize")
async def summarize_text(request: SummaryRequest):
    """
    Generate a summary at the specified level.

    Levels: 1line, bullet, 50w, 150w
    Automatically handles large texts via chunked map-reduce summarization.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    # Check cache first
    key = cache_key(request.text, request.level)
    if key in summary_cache:
        return summary_cache[key]

    try:
        sum_model = get_summarizer()
        result = sum_model.summarize(request.text, request.level)
        # Cache the result
        summary_cache[key] = result
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")


@router.post("/summarize-multi")
async def multi_level_summary(request: SummaryRequest):
    """
    Generate summaries at all levels (1line, bullet, 50w, 150w).
    Automatically handles large texts via chunked map-reduce summarization.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        sum_model = get_summarizer()
        results = sum_model.multi_level_summary(request.text)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")
