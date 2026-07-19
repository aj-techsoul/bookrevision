from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import logging
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Simplifier:
    """Handle text simplification at different reading levels."""
    
    def __init__(self, model_name: str = 'google/flan-t5-small'):
        """
        Initialize simplifier.
        
        Args:
            model_name: Hugging Face model name for text-to-text generation
        """
        self.model_name = model_name
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Using device: {self.device}")
        
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.loading = False
        
        import threading
        threading.Thread(target=self._load_model, daemon=True).start()
    
    def _load_model(self):
        """Load the simplification model in background."""
        if self.loading:
            return
        self.loading = True
        logger.info(f"Loading simplification model: {self.model_name} in background...")
        try:
            # Try local first
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=True)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name, local_files_only=True)
            except OSError:
                logger.info(f"Model {self.model_name} not found locally, downloading from HF...")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=False)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name, local_files_only=False)

            if self.model is not None:
                self.model.to(self.device)
                self.model.eval()  # Set to evaluation mode for faster inference
                logger.info("Simplification model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load simplification model '{self.model_name}' (will use fallback): {e}")
            self.tokenizer = None
            self.model = None
        finally:
            self.loading = False

    def _fallback_simplify_rules(self, text: str) -> str:
        """Rule-based text simplification fallback."""
        import re
        complex_words = {
            'utilize': 'use',
            'demonstrate': 'show',
            'approximately': 'about',
            'subsequently': 'later',
            'consequently': 'so',
            'nevertheless': 'still',
            'furthermore': 'also',
            'moreover': 'also',
            'therefore': 'so',
            'however': 'but',
            'additionally': 'also',
            'significantly': 'greatly',
            'substantial': 'large',
            'numerous': 'many',
            'facilitate': 'help',
            'implement': 'use',
            'commence': 'start',
            'terminate': 'end',
            'ascertain': 'find out',
            'elucidate': 'explain',
            'expedite': 'speed up',
        }
        words = text.split()
        simplified_words = []
        for w in words:
            clean_w = re.sub(r'[^\w]', '', w).lower()
            if clean_w in complex_words:
                replacement = complex_words[clean_w]
                if w[0].isupper():
                    replacement = replacement.capitalize()
                simplified_words.append(w.replace(re.sub(r'[^\w]', '', w), replacement))
            else:
                simplified_words.append(w)
        return ' '.join(simplified_words)

    def simplify(self, 
                 text: str, 
                 level: str = 'high_school',
                 max_length: int = 300) -> Dict[str, str]:
        """
        Simplify text to a specified reading level.
        
        Args:
            text: Input text to simplify
            level: Reading level ('elementary', 'middle_school', 'high_school', 'college')
            max_length: Maximum output length
            
        Returns:
            Dictionary with simplified text and metadata
        """
        level_descriptions = {
            'elementary': 'Explain this as if you were teaching a 10-year-old. Use simple words and short sentences.',
            'middle_school': 'Explain this for a middle school student. Use clear language and avoid jargon.',
            'high_school': 'Explain this for a high school student. Keep it clear but include important details.',
            'college': 'Explain this for a college student. Maintain accuracy while being clear.'
        }
        
        if level not in level_descriptions:
            raise ValueError(f"Unknown reading level: {level}")
        
        prompt = f"{level_descriptions[level]}\n\nText: {text}"
        
        try:
            if self.model is None or self.tokenizer is None:
                raise RuntimeError("Model or tokenizer not loaded. Running fallback.")

            inputs = self.tokenizer(
                prompt,
                max_length=512,
                truncation=True,
                return_tensors='pt'
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=max_length,
                    min_length=50,
                    do_sample=False,
                    early_stopping=True
                )
            
            simplified = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return {
                'simplified_text': simplified,
                'level': level,
                'original_length': len(text.split()),
                'simplified_length': len(simplified.split())
            }
            
        except Exception as e:
            logger.warning(f"Transformer simplification failed: {e}. Falling back to rule-based simplification.")
            try:
                simplified = self._fallback_simplify_rules(text)
                return {
                    'simplified_text': simplified,
                    'level': level,
                    'original_length': len(text.split()),
                    'simplified_length': len(simplified.split())
                }
            except Exception as fallback_err:
                logger.error(f"Fallback simplification failed: {fallback_err}")
                raise
    
    def eli10(self, text: str, max_length: int = 200) -> Dict[str, str]:
        """
        Explain Like I'm 10 - extreme simplification for children.
        
        Args:
            text: Input text to explain
            max_length: Maximum output length
            
        Returns:
            Dictionary with explanation and metadata
        """
        prompt = f"Explain the following concept as if you were teaching a curious 10-year-old. Use a simple analogy. Avoid jargon.\n\nConcept: {text}"
        
        try:
            if self.model is None or self.tokenizer is None:
                raise RuntimeError("Model or tokenizer not loaded. Running fallback.")

            inputs = self.tokenizer(
                prompt,
                max_length=512,
                truncation=True,
                return_tensors='pt'
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=max_length,
                    min_length=30,
                    do_sample=False,
                    early_stopping=True
                )
            
            explanation = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return {
                'explanation': explanation,
                'original_length': len(text.split()),
                'explanation_length': len(explanation.split())
            }
            
        except Exception as e:
            logger.warning(f"Transformer ELI10 failed: {e}. Falling back to rules.")
            try:
                simplified = self._fallback_simplify_rules(text)
                explanation = f"In simple terms: {simplified}. Think of it like a helpful tool that makes things work more simply."
                return {
                    'explanation': explanation,
                    'original_length': len(text.split()),
                    'explanation_length': len(explanation.split())
                }
            except Exception as fallback_err:
                logger.error(f"Fallback ELI10 failed: {fallback_err}")
                raise
    
    def simplify_word(self, word: str) -> Dict[str, str]:
        """
        Provide simpler synonyms for a complex word.
        
        Args:
            word: Complex word to simplify
            
        Returns:
            Dictionary with simpler alternatives
        """
        # Simple word mapping (in production, use WordNet or a dedicated model)
        complex_words = {
            'utilize': 'use',
            'demonstrate': 'show',
            'approximately': 'about',
            'subsequently': 'later',
            'consequently': 'so',
            'nevertheless': 'still',
            'furthermore': 'also',
            'moreover': 'also',
            'therefore': 'so',
            'however': 'but',
            'additionally': 'also',
            'significantly': 'greatly',
            'substantial': 'large',
            'numerous': 'many',
            'facilitate': 'help',
            'implement': 'use',
            'commence': 'start',
            'terminate': 'end',
            'ascertain': 'find out',
            'elucidate': 'explain',
            'expedite': 'speed up',
        }
        
        word_lower = word.lower()
        simpler = complex_words.get(word_lower, word)
        
        return {
            'original': word,
            'simpler': simpler,
            'found': simpler != word
        }
