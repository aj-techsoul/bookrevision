from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, ForeignKey, JSON, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Database URL pointing to v2 clean database
SQLALCHEMY_DATABASE_URL = "sqlite:///./edusummarize_v2.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")  # ~64MB cache
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA foreign_keys=ON")
    except Exception:
        pass
    finally:
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=True)  # Nullable for existing records
    education_level = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="user")
    chat_history = relationship("ChatHistory", back_populates="user")
    quiz_attempts = relationship("QuizAttempt", back_populates="user")
    learning_analytics = relationship("LearningAnalytics", back_populates="user")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    filename = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    page_count = Column(Integer)
    raw_text_path = Column(String)

    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document")
    summaries = relationship("Summary", back_populates="document")
    quizzes = relationship("Quiz", back_populates="document")
    flashcards = relationship("Flashcard", back_populates="document")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, ForeignKey("documents.id"))
    chunk_index = Column(Integer)
    text = Column(Text)
    embedding_vector_id = Column(String)

    # Relationships
    document = relationship("Document", back_populates="chunks")


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, ForeignKey("documents.id"))
    level = Column(String)  # 1line, bullet, 50w, 150w
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="summaries")


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    document_id = Column(String, ForeignKey("documents.id"))
    question = Column(Text)
    answer = Column(Text)
    source_chunk_ids = Column(JSON)  # List of chunk IDs used
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="chat_history")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, ForeignKey("documents.id"))
    question = Column(Text)
    options_json = Column(JSON)  # {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_answer = Column(String)  # "A", "B", "C", or "D"
    difficulty = Column(String)

    # Relationships
    document = relationship("Document", back_populates="quizzes")
    attempts = relationship("QuizAttempt", back_populates="quiz")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    selected_answer = Column(String)
    is_correct = Column(Integer)  # 0 or 1
    attempted_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="quiz_attempts")
    quiz = relationship("Quiz", back_populates="attempts")


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, ForeignKey("documents.id"))
    front = Column(Text)
    back = Column(Text)

    # Relationships
    document = relationship("Document", back_populates="flashcards")


class LearningAnalytics(Base):
    __tablename__ = "learning_analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    topic = Column(String)
    times_reviewed = Column(Integer, default=0)
    avg_quiz_score = Column(Float, default=0.0)
    last_reviewed = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="learning_analytics")


def init_db():
    """Initialize the database."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
