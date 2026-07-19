from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# BART's hard token limit
BART_MAX_INPUT_TOKENS = 1024
# Safe threshold — start chunking if input tokens exceed this
CHUNK_THRESHOLD_TOKENS = 900


class Summarizer:
    """Handle multi-level abstractive summarization with large-text support."""

    def __init__(self, model_name: str = 'sshleifer/distilbart-cnn-6-6'):
        """
        Initialize summarizer.

        Args:
            model_name: Hugging Face model name for summarization
        """
        self.model_name = model_name
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Using device: {self.device}")

        self.tokenizer = None
        self.model = None
        self.loading = False
        
        import threading
        threading.Thread(target=self._load_model, daemon=True).start()

    def _load_model(self):
        """Load the summarization model in background."""
        if self.loading:
            return
        self.loading = True
        logger.info(f"Loading summarization model: {self.model_name} in background...")
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
                logger.info("Summarization model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load summarization model '{self.model_name}' (will use fallback): {e}")
            self.tokenizer = None
            self.model = None
        finally:
            self.loading = False

    def _count_tokens(self, text: str) -> int:
        """Count the number of tokens in text."""
        if self.tokenizer is None:
            return len(text.split())
        try:
            tokens = self.tokenizer(text, return_tensors='pt', truncation=False)
            return tokens.input_ids.shape[1]
        except Exception:
            return len(text.split())

    def _extractive_summarize_fallback(self, text: str, level: str) -> str:
        """Lightweight extractive statistical fallback summary."""
        import re
        from collections import Counter
        
        # Normalize text and split into sentences
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        if not sentences:
            return text
            
        # Count word frequencies to score sentences
        words = re.findall(r'\w+', text.lower())
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'to', 'of', 'in', 'on', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'from', 'up', 'down', 'in', 'out', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves'}
        
        word_freq = Counter(w for w in words if w not in stop_words)
        if not word_freq:
            return sentences[0]
            
        sentence_scores = {}
        for i, sent in enumerate(sentences):
            sent_words = re.findall(r'\w+', sent.lower())
            score = sum(word_freq[w] for w in sent_words if w in word_freq)
            sentence_scores[i] = score / max(1, len(sent_words))
            
        sorted_indices = sorted(sentence_scores.keys(), key=lambda i: sentence_scores[i], reverse=True)
        
        if level == '1line':
            num_sents = 1
        elif level == 'bullet':
            num_sents = min(5, len(sentences))
        elif level == '50w':
            num_sents = min(3, len(sentences))
        else: # '150w'
            num_sents = min(7, len(sentences))
            
        top_indices = sorted(sorted_indices[:num_sents])
        summary_sentences = [sentences[idx] for idx in top_indices]
        
        return ' '.join(summary_sentences)

    def summarize(self,
                  text: str,
                  level: str = '150w') -> Dict[str, str]:
        """
        Generate summary at specified level. Auto-chunks large text.

        Args:
            text: Input text to summarize
            level: Summary level ('1line', 'bullet', '50w', '150w')

        Returns:
            Dictionary with summary and metadata
        """
        level_configs = {
            '1line': {'max_length': 30, 'min_length': 5,  'do_sample': False},
            'bullet': {'max_length': 200, 'min_length': 40, 'do_sample': False},
            '50w':   {'max_length': 70,  'min_length': 20, 'do_sample': False},
            '150w':  {'max_length': 200, 'min_length': 60, 'do_sample': False},
        }

        if level not in level_configs:
            raise ValueError(f"Unknown summary level: {level}. Choose from: {list(level_configs.keys())}")

        config = level_configs[level]

        try:
            token_count = self._count_tokens(text)
            logger.info(f"Input text has {token_count} tokens")

            if self.model is None or self.tokenizer is None:
                raise RuntimeError("Model or tokenizer not loaded. Running fallback.")

            if token_count <= CHUNK_THRESHOLD_TOKENS:
                # Short text — summarize directly
                summary = self._summarize_single(text, config)
            else:
                # Long text — use map-reduce chunking strategy
                logger.info("Text exceeds token threshold — using chunked summarization")
                summary = self._chunked_summarize(text, config, level)

            # Post-process for bullet points
            if level == 'bullet':
                summary = self._format_as_bullets(summary)

            return {
                'summary': summary,
                'level': level,
                'original_length': len(text.split()),
                'summary_length': len(summary.split()),
                'was_chunked': token_count > CHUNK_THRESHOLD_TOKENS,
                'original_tokens': token_count,
            }

        except Exception as e:
            logger.warning(f"Transformer summarization failed: {e}. Falling back to extractive summary.")
            try:
                summary = self._extractive_summarize_fallback(text, level)
                if level == 'bullet':
                    summary = self._format_as_bullets(summary)
                return {
                    'summary': summary,
                    'level': level,
                    'original_length': len(text.split()),
                    'summary_length': len(summary.split()),
                    'was_chunked': False,
                    'original_tokens': len(text.split()),
                }
            except Exception as fallback_err:
                logger.error(f"Fallback summarization also failed: {fallback_err}")
                raise ValueError(f"Summarization failed: {str(e)}")
    def _summarize_single(self, text: str, config: dict) -> str:
        """Summarize a single chunk of text using the transformer model."""
        inputs = self.tokenizer(
            text,
            max_length=BART_MAX_INPUT_TOKENS,
            truncation=True,
            return_tensors='pt'
        ).to(self.device)

        with torch.no_grad():
            summary_ids = self.model.generate(
                inputs.input_ids,
                num_beams=4,
                max_length=config.get('max_length', 150),
                min_length=config.get('min_length', 30),
                early_stopping=True,
                do_sample=config.get('do_sample', False)
            )

        return self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    def _chunked_summarize(self, text: str, config: dict, level: str) -> str:
        """
        Map-Reduce summarization for long texts.
        Step 1 (Map): Summarize each chunk independently.
        Step 2 (Reduce): Summarize the combined chunk summaries.

        Args:
            text: Full long text
            config: Generation config
            level: Summary level string

        Returns:
            Final combined summary
        """
        chunks = self._split_text_into_chunks(text, max_tokens=CHUNK_THRESHOLD_TOKENS)

        if not chunks:
            raise ValueError("Text could not be split into valid chunks")

        # Step 1: Summarize each chunk (use a mid-level config for intermediates)
        intermediate_config = {
            'max_length': 150,
            'min_length': 20,
            'do_sample': False,
        }

        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Summarizing chunk {i + 1}/{len(chunks)}")
            try:
                chunk_summary = self._summarize_single(chunk, intermediate_config)
                chunk_summaries.append(chunk_summary)
            except Exception as e:
                logger.warning(f"Failed to summarize chunk {i + 1}: {e}")

        if not chunk_summaries:
            raise ValueError("All chunk summarizations failed")

        # Step 2: Combine and re-summarize if still too long
        combined = ' '.join(chunk_summaries)
        combined_tokens = self._count_tokens(combined)

        if combined_tokens > CHUNK_THRESHOLD_TOKENS:
            logger.info("Combined summaries still too long — performing final reduction")
            final_summary = self._summarize_single(
                combined[:3000],  # hard safety cap on chars
                config
            )
        else:
            final_summary = self._summarize_single(combined, config)

        return final_summary

    def _format_as_bullets(self, text: str) -> str:
        """Format text as bullet points."""
        import re
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        bullets = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 5:
                bullets.append(f"• {sentence}")
        return '\n'.join(bullets) if bullets else f"• {text}"

    def multi_level_summary(self, text: str) -> Dict[str, Dict[str, str]]:
        """
        Generate summaries at all levels.

        Args:
            text: Input text to summarize

        Returns:
            Dictionary with all summary levels
        """
        levels = ['1line', 'bullet', '50w', '150w']
        summaries = {}

        for level in levels:
            try:
                summaries[level] = self.summarize(text, level)
            except Exception as e:
                logger.error(f"Failed to generate {level} summary: {e}")
                summaries[level] = {'summary': '', 'error': str(e)}

        return summaries

    def summarize_chunks(self, chunks: list, level: str = '150w') -> str:
        """
        Summarize multiple pre-split chunks (for long documents).

        Args:
            chunks: List of text chunks (dicts with 'text' key or plain strings)
            level: Summary level

        Returns:
            Combined summary
        """
        chunk_summaries = []
        for chunk in chunks:
            text = chunk['text'] if isinstance(chunk, dict) else chunk

            try:
                result = self.summarize(text, level)
                chunk_summaries.append(result['summary'])
            except Exception as e:
                logger.error(f"Failed to summarize chunk: {e}")

        combined = ' '.join(chunk_summaries)

        if len(combined.split()) > 300:
            result = self.summarize(combined, level)
            return result['summary']

        return combined
