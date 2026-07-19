from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid
import aiofiles
import sys
from typing import Optional
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.services.document_ingestion import DocumentIngester
from backend.services.text_processor import TextProcessor
from backend import shared_state
from backend.database import get_db, Document as DB_Document, Chunk as DB_Chunk
from backend.api.auth import CRYPTO_AVAILABLE, SECRET_KEY, ALGORITHM

# Try to import jose jwt directly
try:
    from jose import jwt
except ImportError:
    jwt = None

router = APIRouter()

# Per-module ML objects (document ingestion doesn't need embeddings here)
ingester = DocumentIngester()
processor = TextProcessor()

# Use absolute path relative to this file's location (project root / uploads)
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_user_id_from_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    if not authorization:
        return None
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            return None
        if CRYPTO_AVAILABLE and jwt is not None:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload.get("sub")
        else:
            import base64, json
            payload = json.loads(base64.b64decode(token).decode())
            return payload.get("sub")
    except Exception:
        return None


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Upload and process a document.

    Supported formats: PDF, DOCX, TXT
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ingester.supported_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file_ext}'. Supported: {', '.join(ingester.supported_formats)}"
        )

    # Generate unique document ID
    doc_id = str(uuid.uuid4())

    # Save uploaded file using absolute path
    file_path = UPLOAD_DIR / f"{doc_id}{file_ext}"

    # Limit file size to 10MB
    MAX_SIZE = 10 * 1024 * 1024

    try:
        total_size = 0
        async with aiofiles.open(file_path, 'wb') as f:
            # Stream file in 1MB chunks to support large PDFs
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_SIZE:
                    raise HTTPException(status_code=400, detail="File size exceeds the 10MB limit.")
                await f.write(chunk)

        # Extract text
        text, metadata = ingester.extract_text(str(file_path), file_ext)

        if not text or not text.strip():
            raise ValueError("No readable text could be extracted from the document. "
                             "If it is a scanned PDF, ensure Tesseract OCR is installed.")

        # Clean text
        cleaned_text = ingester.clean_text(text)

        # Preprocess
        processed_text = processor.preprocess(cleaned_text)

        # Chunk text
        chunks = processor.chunk_text(processed_text)

        # Store the full processed text for later summarization
        # Save text to outputs dir so summary endpoint can use it
        text_path = UPLOAD_DIR.parent / "outputs" / f"{doc_id}.txt"
        text_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(text_path, 'w', encoding='utf-8') as tf:
            await tf.write(processed_text)

        # Generate embeddings using shared model
        emb_model = shared_state.get_embedding_model()
        chunks_with_embeddings = emb_model.embed_chunks(chunks)

        # Store in SHARED vector database so chat can find them
        vdb = shared_state.get_vector_db()
        embeddings = [chunk['embedding'] for chunk in chunks_with_embeddings]
        chunk_metadata = [
            {
                'chunk_index': chunk['chunk_index'],
                'text': chunk['text'],
                'document_id': doc_id,
                'word_count': chunk['word_count']
            }
            for chunk in chunks_with_embeddings
        ]

        vdb.add_embeddings(embeddings, chunk_metadata)

        # Track the uploaded document in shared state
        shared_state.uploaded_documents[doc_id] = file.filename

        # Get authenticated user if token is present
        user_id = get_user_id_from_token(authorization)

        # Persist document metadata in SQLAlchemy SQLite database
        db_doc = DB_Document(
            id=doc_id,
            user_id=user_id,
            filename=file.filename,
            page_count=metadata.get('page_count', 1),
            raw_text_path=str(text_path)
        )
        db.add(db_doc)

        # Persist chunks in database
        for chunk in chunks_with_embeddings:
            db_chunk = DB_Chunk(
                document_id=doc_id,
                chunk_index=chunk['chunk_index'],
                text=chunk['text'],
                embedding_vector_id=None
            )
            db.add(db_chunk)

        db.commit()

        # Calculate reading time
        reading_time = processor.estimate_reading_time(processed_text)

        return JSONResponse({
            "document_id": doc_id,
            "filename": file.filename,
            "file_type": file_ext,
            "metadata": metadata,
            "full_text": processed_text[:5000],   # Preview (first 5000 chars)
            "full_text_truncated": len(processed_text) > 5000,
            "stats": {
                "total_chunks": len(chunks),
                "total_words": processor.count_words(processed_text),
                "total_chars": len(processed_text),
                "estimated_reading_time_minutes": reading_time
            },
            "message": "Document processed successfully"
        })

    except HTTPException:
        if file_path.exists():
            file_path.unlink()
        raise

    except Exception as e:
        # Clean up on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
