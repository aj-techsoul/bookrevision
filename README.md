# EduSummarize AI

An Intelligent AI Chatbot for Automatic Note Summarization and Simplified Learning.

## Features

- **Document Upload**: Support for PDF, DOCX, and TXT files with OCR for scanned documents.

- **Multi-Level Summarization**: Generate summaries at different levels (1-line, bullet points, 50-word, 150-word)
- **Text Simplification**: Simplify complex text to different reading levels (elementary to college)
- **Explain Like I'm 10**: Extreme simplification for children using simple analogies
- **RAG Chatbot**: Ask questions about your uploaded documents with source citations
- **Keyword Extraction**: Extract important keywords and key phrases from text
- **Quiz Generation**: Auto-generate MCQ quizzes from your notes
- **Flashcard Generation**: Create study flashcards automatically
- **Reading Time Estimation**: Calculate how long it takes to read documents

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **PyTorch + Transformers**: Deep learning framework and Hugging Face models
- **FAISS**: Vector database for efficient similarity search
- **Sentence-Transformers**: Text embeddings using MiniLM
- **SQLAlchemy**: Database ORM
- **PyMuPDF / pdfplumber / python-docx**: Document text extraction
- **Tesseract**: OCR for scanned documents

### Frontend
- **React**: Modern UI library
- **Material-UI (MUI)**: React component library
- **Axios**: HTTP client for API requests
- **React Router**: Client-side routing

### ML Models
- **facebook/bart-large-cnn**: Abstractive summarization
- **google/flan-t5-base**: Text simplification and instruction following
- **all-MiniLM-L6-v2**: Text embeddings (384 dimensions)

## Installation

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- Git

### Backend Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd project11
```

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Linux/Mac
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Download spaCy model:
```bash
python -m spacy download en_core_web_sm
```

5. Install Tesseract OCR (for scanned PDF support):
- Windows: Download from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
- Linux: `sudo apt-get install tesseract-ocr`
- Mac: `brew install tesseract`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install Node dependencies:
```bash
npm install
```

## Running the Application

### Start Backend

From the project root:
```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### Start Frontend

From the frontend directory:
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

### Document Upload
- `POST /api/upload` - Upload and process a document

### Summarization
- `POST /api/summary/summarize` - Generate summary at a specific level
- `POST /api/summary/summarize-multi` - Generate summaries at all levels

### Simplification
- `POST /api/simplify/simplify` - Simplify text to a reading level
- `POST /api/simplify/eli10` - Explain Like I'm 10
- `POST /api/simplify/simplify-word` - Get simpler synonyms for a word

### Chat
- `POST /api/chat/chat` - Ask a question about uploaded documents

### Keywords
- `POST /api/keywords/extract` - Extract keywords
- `POST /api/keywords/extract-phrases` - Extract key phrases

### Quiz
- `POST /api/quiz/generate` - Generate MCQ quiz

### Flashcards
- `POST /api/flashcards/generate` - Generate flashcards

## Project Structure

```
EduSummarizeAI/
├── backend/
│   ├── api/                 # FastAPI route handlers
│   ├── services/            # Business logic
│   ├── main.py              # Application entry point
│   └── database.py          # Database models
├── frontend/                # React application
│   ├── src/
│   │   ├── components/      # React components
│   │   └── App.js           # Main app component
│   └── package.json
├── models/                  # ML model wrappers
├── summarizer/              # Summarization logic
├── simplifier/              # Text simplification
├── chatbot/                 # RAG chatbot
├── quiz_generator/          # Quiz generation
├── flashcards/              # Flashcard generation
├── embeddings/              # Embedding generation
├── vectorDB/                # FAISS index files
├── uploads/                 # Uploaded files
├── outputs/                 # Generated exports
└── requirements.txt         # Python dependencies
```

## Usage

1. **Upload a Document**: Go to the Upload tab and select a PDF, DOCX, or TXT file
2. **Generate Summary**: Paste text or use uploaded document to generate multi-level summaries
3. **Simplify Text**: Enter complex text and simplify it to different reading levels
4. **Chat with Notes**: Ask questions about your uploaded documents
5. **Generate Quiz**: Create MCQ quizzes from your notes
6. **Create Flashcards**: Generate study flashcards automatically
7. **Extract Keywords**: Find important keywords and phrases

## Database Schema

The application uses SQLite with the following tables：
- `users` - User information
- `documents` - Uploaded document metadata
- `chunks` - Text chunks with embeddings
- `summaries` - Generated summaries
- `chat_history` - Chat conversation history
- `quizzes` - Generated quizzes
- `quiz_attempts` - User quiz attempts
- `flashcards` - Generated flashcards
- `learning_analytics` - User learning progress

## Evaluation Metrics

The system supports evaluation using:
- **ROUGE**: For summarization quality
- **BERTScore**: For semantic similarity
- **SARI**: For text simplification
- **FKGL**: For readability assessment
- **EM/F1**: For question answering accuracy

## Future Enhancements

- Voice input/output using Whisper and TTS
- Multi-language support
- Teacher dashboard for class analytics
- Automatic citation generation
- Offline mode with quantized models
- Mind map visualization

## License

This project is for educational purposes.

## Contributing

This is a final-year B.Tech CSE major project. Contributions are welcome for research and development purposes.
