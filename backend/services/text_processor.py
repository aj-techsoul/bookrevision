import re
import nltk
from typing import List, Tuple
import logging

# Download required NLTK data (graceful offline fallback)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    try:
        nltk.download('punkt', quiet=True)
    except Exception:
        pass

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    try:
        nltk.download('punkt_tab', quiet=True)
    except Exception:
        pass

try:
    nltk.data.find('stopwords')
except LookupError:
    try:
        nltk.download('stopwords', quiet=True)
    except Exception:
        pass

try:
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextProcessor:
    """Handle text preprocessing and chunking."""
    
    def __init__(self):
        if NLTK_AVAILABLE:
            try:
                self.stop_words = set(stopwords.words('english'))
            except Exception:
                self.stop_words = set()
        else:
            self.stop_words = set()
    
    def preprocess(self, text: str) -> str:
        """
        Preprocess text for ML models.
        
        Args:
            text: Raw text
            
        Returns:
            Preprocessed text
        """
        # Basic cleaning
        text = self.clean_text(text)
        
        # For transformer models, we generally don't remove stopwords
        # or do stemming/lemmatization as they expect natural text
        # This method keeps text natural for transformers
        
        return text
    
    def clean_text(self, text: str) -> str:
        """Clean text by removing artifacts."""
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Fix common PDF extraction artifacts
        text = re.sub(r'(\w)\-(\s)(\w)', r'\1-\3', text)  # Fix hyphenated words
        text = re.sub(r'(\d+)\.(\d+)', r'\1.\2', text)  # Fix decimal numbers
        
        # Normalize spaces per-line
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            line = re.sub(r'[ \t]+', ' ', line)
            cleaned_lines.append(line)
            
        text = '\n'.join(cleaned_lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def chunk_text(self, 
                   text: str, 
                   chunk_size: int = 400, 
                   overlap: float = 0.15) -> List[dict]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Input text
            chunk_size: Target chunk size in tokens (approximate)
            overlap: Overlap fraction (0.15 = 15%)
            
        Returns:
            List of chunks with metadata
        """
        try:
            sentences = sent_tokenize(text)
        except Exception:
            # Regex sentence tokenizer fallback
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        overlap_sentences = int(chunk_size * overlap / 10)  # Approximate overlap in sentences
        
        for i, sentence in enumerate(sentences):
            try:
                sentence_words = len(word_tokenize(sentence))
            except Exception:
                sentence_words = len(sentence.split())
            
            # If adding this sentence exceeds chunk size and we have content
            if current_length + sentence_words > chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'chunk_index': len(chunks),
                    'sentence_count': len(current_chunk),
                    'word_count': current_length
                })
                
                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk) - overlap_sentences)
                current_chunk = current_chunk[overlap_start:]
                try:
                    current_length = sum(len(word_tokenize(s)) for s in current_chunk)
                except Exception:
                    current_length = sum(len(s.split()) for s in current_chunk)
            
            current_chunk.append(sentence)
            current_length += sentence_words
        
        # Add final chunk if it has content
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'chunk_index': len(chunks),
                'sentence_count': len(current_chunk),
                'word_count': current_length
            })
        
        logger.info(f"Chunked text into {len(chunks)} chunks")
        return chunks
    
    def extract_sentences(self, text: str) -> List[str]:
        """Extract individual sentences from text."""
        try:
            return sent_tokenize(text)
        except Exception:
            return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    
    def count_words(self, text: str) -> int:
        """Count words in text."""
        try:
            return len(word_tokenize(text))
        except Exception:
            return len(text.split())
    
    def estimate_reading_time(self, text: str, wpm: int = 200) -> int:
        """
        Estimate reading time in minutes.
        
        Args:
            text: Input text
            wpm: Average reading speed (words per minute)
            
        Returns:
            Estimated reading time in minutes
        """
        word_count = self.count_words(text)
        return max(1, round(word_count / wpm))
