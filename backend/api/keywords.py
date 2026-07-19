from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.services.keyword_extractor import KeywordExtractor

router = APIRouter()

# Global keyword extractor instance
keyword_extractor = KeywordExtractor(method='tfidf')

class KeywordsRequest(BaseModel):
    text: str
    top_n: int = 10

@router.post("/extract")
async def extract_keywords(request: KeywordsRequest):
    """
    Extract keywords from text.
    """
    try:
        keywords = keyword_extractor.extract_keywords(request.text, request.top_n)
        return {"keywords": keywords}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Keyword extraction failed: {str(e)}")

@router.post("/extract-phrases")
async def extract_key_phrases(request: KeywordsRequest):
    """
    Extract key phrases (multi-word expressions) from text.
    """
    try:
        phrases = keyword_extractor.extract_key_phrases(request.text, request.top_n)
        return {"phrases": phrases}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Phrase extraction failed: {str(e)}")
