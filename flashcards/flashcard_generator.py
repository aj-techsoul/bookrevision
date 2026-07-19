from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import logging
from typing import List, Dict
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FlashcardGenerator:
    """Generate flashcards from text."""
    
    def __init__(self, model_name: str = 'google/flan-t5-small'):
        """
        Initialize flashcard generator.
        
        Args:
            model_name: Hugging Face model name
        """
        self.model_name = model_name
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        self.tokenizer = None
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the generation model."""
        logger.info(f"Loading flashcard generation model: {self.model_name}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()  # Set to evaluation mode for faster inference
        
        logger.info("Flashcard generation model loaded")
    
    def generate_flashcards(self, 
                           text: str, 
                           num_cards: int = 10) -> List[Dict]:
        """
        Generate flashcards from text.
        
        Args:
            text: Source text
            num_cards: Number of flashcards to generate
            
        Returns:
            List of flashcard dictionaries with 'front' and 'back'
        """
        flashcards = []
        
        # Split text into chunks
        chunks = self._split_text(text, num_chunks=num_cards)
        
        for i, chunk in enumerate(chunks):
            try:
                card = self._generate_single_flashcard(chunk)
                if card:
                    flashcards.append(card)
                    
                if len(flashcards) >= num_cards:
                    break
                    
            except Exception as e:
                logger.error(f"Failed to generate flashcard {i}: {e}")
        
        return flashcards
    
    def _split_text(self, text: str, num_chunks: int) -> List[str]:
        """Split text into chunks for flashcard generation."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunk_size = max(1, len(sentences) // num_chunks)
        chunks = []
        
        for i in range(0, len(sentences), chunk_size):
            chunk = ' '.join(sentences[i:i+chunk_size])
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def _generate_single_flashcard(self, text: str) -> Dict:
        """Generate a single flashcard (Q&A pair)."""
        prompt = f"""Create a flashcard from the following text. 
The front should be a question or key term, and the back should be the answer or definition.
Format as: Front: [question] | Back: [answer]

Text: {text}"""
        
        try:
            inputs = self.tokenizer(
                prompt,
                max_length=512,
                truncation=True,
                return_tensors='pt'
            ).to(self.device)
            
            outputs = self.model.generate(
                inputs.input_ids,
                max_length=150,
                do_sample=False,
                early_stopping=True
            )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Parse the response
            return self._parse_flashcard_response(response, text)
            
        except Exception as e:
            logger.error(f"Flashcard generation failed: {e}")
            return self._create_fallback_flashcard(text)
    
    def _parse_flashcard_response(self, response: str, original_text: str) -> Dict:
        """Parse the model response into front/back format."""
        # Try to extract Front and Back
        front_match = re.search(r'Front:\s*(.+?)(?:\||Back:|$)', response, re.IGNORECASE)
        back_match = re.search(r'Back:\s*(.+?)$', response, re.IGNORECASE)
        
        front = front_match.group(1).strip() if front_match else ""
        back = back_match.group(1).strip() if back_match else ""
        
        if front and back:
            return {'front': front, 'back': back}
        
        # Fallback: create from text
        return self._create_fallback_flashcard(original_text)
    
    def _create_fallback_flashcard(self, text: str) -> Dict:
        """Create a simple fallback flashcard."""
        words = text.split()
        if len(words) < 3:
            return None
        
        # Take first meaningful phrase as front
        front = ' '.join(words[:5])
        
        # Rest as back
        back = ' '.join(words[5:15]) if len(words) > 5 else text
        
        return {
            'front': f"What is: {front}?",
            'back': back[:200]
        }
    
    def generate_from_keywords(self, keywords: List[Dict], text: str) -> List[Dict]:
        """
        Generate flashcards from extracted keywords.
        
        Args:
            keywords: List of keyword dictionaries
            text: Source text for context
            
        Returns:
            List of flashcards
        """
        flashcards = []
        
        for kw in keywords[:10]:
            word = kw.get('word', '')
            if word:
                # Find sentence containing the keyword
                sentences = re.split(r'[.!?]+', text)
                definition = ""
                
                for sentence in sentences:
                    if word.lower() in sentence.lower():
                        definition = sentence.strip()
                        break
                
                if definition:
                    flashcards.append({
                        'front': f"Define: {word}",
                        'back': definition
                    })
        
        return flashcards
