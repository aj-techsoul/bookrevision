from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.api import upload, summary, simplify, keywords, quiz, flashcards, auth
from backend.database import init_db

# Initialize DB on startup
init_db()

# Create app
app = FastAPI(
    title="bookrevision",
    description="An Intelligent AI Chatbot for Automatic Note Summarization and Simplified Learning",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
for dir_name in ["uploads", "outputs"]:
    Path(dir_name).mkdir(exist_ok=True)

# Include API routers
app.include_router(auth.router,       prefix="/api/auth",      tags=["auth"])
app.include_router(upload.router,     prefix="/api",           tags=["upload"])
app.include_router(summary.router,    prefix="/api/summary",   tags=["summary"])
app.include_router(simplify.router,   prefix="/api/simplify",  tags=["simplify"])

app.include_router(keywords.router,   prefix="/api/keywords",  tags=["keywords"])
app.include_router(quiz.router,       prefix="/api/quiz",      tags=["quiz"])
app.include_router(flashcards.router, prefix="/api/flashcards",tags=["flashcards"])


@app.get("/")
async def root():
    return {
        "message": "EduSummarize AI API",
        "version": "1.0.0",
        "endpoints": {
            "auth_signup": "/api/auth/signup",
            "auth_signin": "/api/auth/signin",
            "upload": "/api/upload",
            "summarize": "/api/summary/summarize",
            "multi_summarize": "/api/summary/summarize-multi",
            "simplify": "/api/simplify/simplify",
            "eli10": "/api/simplify/eli10",
            "simplify_word": "/api/simplify/simplify-word",

            "keywords": "/api/keywords/extract",
            "key_phrases": "/api/keywords/extract-phrases",
            "quiz": "/api/quiz/generate",
            "flashcards": "/api/flashcards/generate"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
