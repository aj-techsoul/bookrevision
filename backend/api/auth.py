from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import uuid
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.database import get_db, User, init_db

router = APIRouter()

# Try to import bcrypt and jose — graceful fallback if not installed
try:
    import bcrypt as _bcrypt
    from jose import JWTError, jwt
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

SECRET_KEY = "edusummarize-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


import re
import hashlib
import secrets

EMAIL_REGEX = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"


def hash_password_fallback(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"pbkdf2_sha256:100000:{salt}:{key.hex()}"


def verify_password_fallback(plain: str, hashed: str) -> bool:
    if hashed.startswith('pbkdf2_sha256:'):
        try:
            parts = hashed.split(':')
            if len(parts) == 4:
                _, iterations, salt, key_hex = parts
                iterations = int(iterations)
                key = hashlib.pbkdf2_hmac(
                    'sha256',
                    plain.encode('utf-8'),
                    salt.encode('utf-8'),
                    iterations
                )
                return key.hex() == key_hex
        except Exception:
            return False
    return False


def hash_password(password: str) -> str:
    if not CRYPTO_AVAILABLE:
        return hash_password_fallback(password)
    try:
        salt = _bcrypt.gensalt()
        hashed = _bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception:
        return hash_password_fallback(password)


def verify_password(plain: str, hashed: str) -> bool:
    if hashed.startswith('plain:'):
        return hashed == f"plain:{plain}"
    if hashed.startswith('pbkdf2_sha256:'):
        return verify_password_fallback(plain, hashed)
    
    if not CRYPTO_AVAILABLE:
        return False
        
    try:
        return _bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return verify_password_fallback(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": int(expire.timestamp())})
    if CRYPTO_AVAILABLE:
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    # Fallback token (not secure — dev only)
    import base64, json
    return base64.b64encode(json.dumps(to_encode).encode()).decode()


class SignUpRequest(BaseModel):
    name: str
    email: str
    password: str
    education_level: Optional[str] = "undergraduate"


class SignInRequest(BaseModel):
    email: str
    password: str


@router.post("/signup")
async def sign_up(request: SignUpRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    # Ensure DB tables exist
    init_db()

    # Validate empty input
    if not request.name.strip() or not request.email.strip() or not request.password:
        raise HTTPException(status_code=400, detail="Please fill in all required fields.")

    # Email format validation
    if not re.match(EMAIL_REGEX, request.email):
        raise HTTPException(status_code=400, detail="Invalid email address.")

    # Password strength check
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password is too weak.")

    # Check if email already registered
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists.")

    user = User(
        id=str(uuid.uuid4()),
        name=request.name.strip(),
        email=request.email.strip().lower(),
        password_hash=hash_password(request.password),
        education_level=request.education_level,
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email})

    return {
        "message": "Account created successfully.",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "education_level": user.education_level,
        },
        "access_token": token,
        "token_type": "bearer",
    }


@router.post("/signin")
async def sign_in(request: SignInRequest, db: Session = Depends(get_db)):
    """Authenticate and return a token."""
    init_db()

    user = db.query(User).filter(User.email == request.email).first()
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.id, "email": user.email})

    return {
        "message": "Signed in successfully",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "education_level": user.education_level,
        },
        "access_token": token,
        "token_type": "bearer",
    }


@router.get("/me")
async def get_current_user_info(token: str, db: Session = Depends(get_db)):
    """Get current user info from token (simple version)."""
    try:
        if CRYPTO_AVAILABLE:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
        else:
            import base64, json
            payload = json.loads(base64.b64decode(token).decode())
            user_id = payload.get("sub")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "education_level": user.education_level,
            "created_at": str(user.created_at),
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
