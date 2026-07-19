import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Concept:
    """Represents a concept extracted from text."""
    type: str  # 'definition', 'abbreviation', 'process', 'advantage', 'disadvantage', 'example', 'application', 'comparison'
    text: str
    context: str
    confidence: float
    subject: str = ""
    predicate: str = ""


class ConceptExtractor:
    """Extract key concepts from text for intelligent quiz generation."""
    
    def __init__(self):
        self.patterns = {
            # Definition patterns
            'definition': [
                r'\b(\w+(?:\s+\w+){0,3})\s+(?:is defined as|refers to|means|can be defined as|represents|is)\s+([^.]+)',
                r'\b(\w+(?:\s+\w+){0,3})\s*:\s*([^.]+)',
            ],
            # Abbreviation patterns
            'abbreviation': [
                r'\b([A-Z]{2,}(?:\s+[A-Z]{2,})*)\s+(?:stands for|is short for|means|represents)\s+([^.]+)',
                r'\b([A-Z]{2,}(?:\s+[A-Z]{2,})*)\s*=\s*([^.]+)',
            ],
            # Process/step patterns
            'process': [
                r'(?:first|second|third|next|then|finally|after|before)\s*,?\s*([^.]+)',
                r'(?:step|phase|stage)\s+\d+\s*:\s*([^.]+)',
                r'\b(\w+(?:\s+\w+){0,3})\s+(?:involves|includes|consists of|requires)\s+([^.]+)',
            ],
            # Advantage patterns
            'advantage': [
                r'(?:advantage|benefit|pro|strength)\s+(?:of|is|:)\s*([^.]+)',
                r'(?:one of the main|a key|an important)\s+(?:advantage|benefit)\s+(?:of|is)\s+([^.]+)',
            ],
            # Disadvantage patterns
            'disadvantage': [
                r'(?:disadvantage|drawback|con|weakness|limitation)\s+(?:of|is|:)\s*([^.]+)',
                r'(?:one of the main|a key|an important)\s+(?:disadvantage|drawback|limitation)\s+(?:of|is)\s+([^.]+)',
            ],
            # Example patterns
            'example': [
                r'(?:example|instance|case)\s+(?:of|is|:)\s*([^.]+)',
                r'(?:for example|for instance|such as)\s*,?\s*([^.]+)',
                r'(?:including|like)\s+([^.]+)',
            ],
            # Application patterns
            'application': [
                r'(?:used|applied|utilized)\s+(?:in|for|to)\s+([^.]+)',
                r'(?:application|use|usage)\s+(?:of|is|:)\s*([^.]+)',
                r'(?:commonly|widely|frequently)\s+used\s+(?:in|for)\s+([^.]+)',
            ],
            # Comparison patterns
            'comparison': [
                r'(?:different|similar|unlike|like|compared to)\s+(?:from|than|with)\s+([^.]+)',
                r'(?:difference|similarity)\s+(?:between|of)\s+([^.]+)',
                r'(?:while|whereas|although)\s+([^.]+)',
            ],
        }
    
    def extract_concepts(self, text: str) -> List[Concept]:
        """
        Extract concepts from text using pattern matching.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of extracted concepts
        """
        concepts = []
        # Split sentences by simple punctuation, keeping track of original context
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 12:
                continue
            
            # Try each pattern type
            for concept_type, patterns in self.patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, sentence, re.IGNORECASE)
                    for match in matches:
                        concept_text = match.group(0)
                        context = sentence
                        
                        # Calculate confidence based on match quality
                        confidence = self._calculate_confidence(match, concept_type, sentence)
                        
                        if confidence > 0.25:  # Minimum confidence threshold
                            groups = match.groups()
                            subject = ""
                            predicate = ""
                            
                            if len(groups) >= 2:
                                subject = groups[0].strip()
                                predicate = groups[1].strip()
                            elif len(groups) == 1:
                                predicate = groups[0].strip()
                                # Infer subject from text before match or use first 3 words of sentence
                                match_start = match.start()
                                pre_text = sentence[:match_start].strip()
                                if pre_text:
                                    words = pre_text.split()
                                    subject = " ".join(words[-2:]) if len(words) >= 2 else words[-1]
                                else:
                                    # Fallback: extract first few words of the sentence
                                    words = sentence.split()
                                    subject = " ".join(words[:2]) if len(words) >= 2 else "Concept"
                            
                            # Clean up subject (strip non-alphanumeric at start/end)
                            subject = re.sub(r'^[^\w]+|[^\w]+$', '', subject).strip()
                            predicate = predicate.strip()
                            
                            if subject and predicate and len(subject) > 2 and len(predicate) > 5:
                                concepts.append(Concept(
                                    type=concept_type,
                                    text=concept_text,
                                    context=context,
                                    confidence=confidence,
                                    subject=subject,
                                    predicate=predicate
                                ))
        
        # Remove duplicates and sort by confidence
        unique_concepts = self._deduplicate_concepts(concepts)
        unique_concepts.sort(key=lambda c: c.confidence, reverse=True)
        
        logger.info(f"Extracted {len(unique_concepts)} concepts from text")
        return unique_concepts[:50]  # Return top 50 concepts
    
    def _calculate_confidence(self, match: re.Match, concept_type: str, sentence: str) -> float:
        """Calculate confidence score for a concept match."""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for longer matches
        match_length = len(match.group(0))
        confidence += min(0.2, match_length / 100)
        
        # Boost confidence for sentences with key indicators
        indicators = {
            'definition': ['is defined as', 'refers to', 'means that'],
            'abbreviation': ['stands for', 'is short for', 'represents'],
            'process': ['involves', 'consists of', 'requires'],
            'advantage': ['advantage is', 'benefit of', 'strength'],
            'disadvantage': ['disadvantage is', 'drawback of', 'limitation'],
            'example': ['for example', 'such as', 'including'],
            'application': ['used in', 'applied to', 'utilized for'],
            'comparison': ['different from', 'similar to', 'compared with'],
        }
        
        for indicator in indicators.get(concept_type, []):
            if indicator.lower() in sentence.lower():
                confidence += 0.15
                break
        
        # Penalize very short sentences
        if len(sentence) < 20:
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def _deduplicate_concepts(self, concepts: List[Concept]) -> List[Concept]:
        """Remove duplicate concepts based on text similarity."""
        seen = set()
        unique = []
        
        for concept in concepts:
            # Normalize subject for comparison
            normalized = concept.subject.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                unique.append(concept)
        
        return unique
    
    def get_concepts_by_type(self, concepts: List[Concept], concept_type: str) -> List[Concept]:
        """Get concepts of a specific type."""
        return [c for c in concepts if c.type == concept_type]
    
    def get_top_concepts(self, concepts: List[Concept], n: int = 10) -> List[Concept]:
        """Get top N concepts by confidence."""
        return concepts[:n]
