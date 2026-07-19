from sklearn.feature_extraction.text import TfidfVectorizer
import spacy
import logging
from typing import List, Dict
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KeywordExtractor:
    """Extract keywords from text using multiple methods."""
    
    def __init__(self, method: str = 'tfidf'):
        """
        Initialize keyword extractor.
        
        Args:
            method: Extraction method ('tfidf', 'spacy', 'combined')
        """
        self.method = method
        
        if method in ['spacy', 'combined']:
            try:
                self.nlp = spacy.load('en_core_web_sm')
                logger.info("Loaded spaCy model")
            except OSError:
                logger.warning("spaCy model not found, falling back to TF-IDF")
                self.method = 'tfidf'
                self.nlp = None
        else:
            self.nlp = None
    
    def extract_keywords(self, 
                        text: str, 
                        top_n: int = 10) -> List[Dict[str, any]]:
        """
        Extract top keywords from text.
        
        Args:
            text: Input text
            top_n: Number of keywords to return
            
        Returns:
            List of keyword dictionaries with word and score
        """
        if self.method == 'tfidf':
            return self._extract_tfidf(text, top_n)
        elif self.method == 'spacy':
            return self._extract_spacy(text, top_n)
        elif self.method == 'combined':
            return self._extract_combined(text, top_n)
        else:
            raise ValueError(f"Unknown method: {self.method}")
    
    def _extract_tfidf(self, text: str, top_n: int) -> List[Dict[str, any]]:
        """Extract keywords using TF-IDF."""
        # Split text into sentences for better TF-IDF
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        if not sentences:
            return []
        
        try:
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 2)  # Include bigrams
            )
            
            tfidf_matrix = vectorizer.fit_transform(sentences)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get average TF-IDF score for each term across all sentences
            mean_scores = tfidf_matrix.mean(axis=0).A1
            
            # Get top keywords
            top_indices = mean_scores.argsort()[-top_n:][::-1]
            
            keywords = []
            for idx in top_indices:
                keywords.append({
                    'word': feature_names[idx],
                    'score': float(mean_scores[idx])
                })
            
            return keywords
            
        except Exception as e:
            logger.error(f"TF-IDF extraction failed: {e}")
            return []
    
    def _extract_spacy(self, text: str, top_n: int) -> List[Dict[str, any]]:
        """Extract keywords using spaCy."""
        if self.nlp is None:
            return self._extract_tfidf(text, top_n)
        
        doc = self.nlp(text)
        
        # Extract nouns and proper nouns as keywords
        keywords = []
        seen = set()
        
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop:
                word = token.text.lower()
                if word not in seen and len(word) > 2:
                    keywords.append({
                        'word': token.text,
                        'score': 1.0,  # spaCy doesn't provide scores
                        'pos': token.pos_
                    })
                    seen.add(word)
        
        return keywords[:top_n]
    
    def _extract_combined(self, text: str, top_n: int) -> List[Dict[str, any]]:
        """Combine TF-IDF and spaCy results."""
        tfidf_keywords = self._extract_tfidf(text, top_n * 2)
        spacy_keywords = self._extract_spacy(text, top_n * 2)
        
        # Combine and deduplicate
        combined = {}
        
        for kw in tfidf_keywords:
            word = kw['word'].lower()
            combined[word] = {
                'word': kw['word'],
                'score': kw['score'],
                'method': 'tfidf'
            }
        
        for kw in spacy_keywords:
            word = kw['word'].lower()
            if word in combined:
                combined[word]['score'] = max(combined[word]['score'], 0.8)
                combined[word]['method'] = 'combined'
            else:
                combined[word] = {
                    'word': kw['word'],
                    'score': 0.8,
                    'method': 'spacy'
                }
        
        # Sort by score and return top_n
        sorted_keywords = sorted(
            combined.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        return sorted_keywords[:top_n]
    
    def extract_key_phrases(self, text: str, top_n: int = 5) -> List[str]:
        """
        Extract key phrases (multi-word expressions).
        
        Args:
            text: Input text
            top_n: Number of phrases to return
            
        Returns:
            List of key phrases
        """
        if self.nlp is None:
            # Fallback to TF-IDF bigrams
            keywords = self._extract_tfidf(text, top_n * 2)
            phrases = [kw['word'] for kw in keywords if ' ' in kw['word']]
            return phrases[:top_n]
        
        doc = self.nlp(text)
        
        # Extract noun phrases
        phrases = []
        seen = set()
        
        for chunk in doc.noun_chunks:
            phrase = chunk.text.strip().lower()
            if len(phrase.split()) > 1 and phrase not in seen and len(phrase) > 5:
                phrases.append(chunk.text)
                seen.add(phrase)
        
        return phrases[:top_n]
