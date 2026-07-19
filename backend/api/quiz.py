from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys
import hashlib
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from quiz_generator.quiz_generator import QuizGenerator

router = APIRouter()

# Global quiz generator instance (lazy loaded)
quiz_generator = None

# Simple in-memory cache
quiz_cache = {}

def get_quiz_generator():
    global quiz_generator
    if quiz_generator is None:
        quiz_generator = QuizGenerator()
    return quiz_generator

def cache_key(text: str, num_questions: int, difficulty: str) -> str:
    """Generate cache key from text and parameters."""
    return hashlib.md5(f"{text}_{num_questions}_{difficulty}".encode()).hexdigest()

class QuizRequest(BaseModel):
    text: str
    num_questions: int = 5
    difficulty: str = "medium"

@router.post("/generate")
async def generate_quiz(request: QuizRequest):
    """
    Generate an MCQ quiz from text.
    """
    # Check cache first
    key = cache_key(request.text, request.num_questions, request.difficulty)
    if key in quiz_cache:
        return quiz_cache[key]

    try:
        qg = get_quiz_generator()
        quiz = qg.generate_quiz(
            request.text,
            num_questions=request.num_questions,
            difficulty=request.difficulty
        )
        result = {"quiz": quiz}
        # Cache the result
        quiz_cache[key] = result
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")
