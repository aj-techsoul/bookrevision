from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import json
import logging
from typing import List, Dict, Optional, Tuple
import re
import random

try:
    from quiz_generator.concept_extractor import ConceptExtractor, Concept
except ModuleNotFoundError:
    from concept_extractor import ConceptExtractor, Concept

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuizGenerator:
    """Generate MCQ quizzes from text with high-quality conceptual questions."""
    
    def __init__(self, model_name: str = 'google/flan-t5-small'):
        """
        Initialize quiz generator.
        
        Args:
            model_name: Hugging Face model name
        """
        self.model_name = model_name
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        self.tokenizer = None
        self.model = None
        self.loading = False
        
        import threading
        threading.Thread(target=self._load_model, daemon=True).start()
        self.concept_extractor = ConceptExtractor()
    
    def _load_model(self):
        """Load the generation model in background."""
        if self.loading:
            return
        self.loading = True
        logger.info(f"Loading quiz generation model: {self.model_name} in background...")
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
                logger.info("Quiz generation model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load quiz model '{self.model_name}' (will use fallback): {e}")
            self.tokenizer = None
            self.model = None
        finally:
            self.loading = False
    
    def generate_quiz(self, 
                      text: str, 
                      num_questions: int = 5,
                      difficulty: str = 'medium') -> List[Dict]:
        """
        Generate a quiz from text.
        
        Args:
            text: Source text
            num_questions: Number of questions to generate
            difficulty: Difficulty level ('easy', 'medium', 'hard')
            
        Returns:
            List of question dictionaries
        """
        # Count words and sentences
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Check if text is too small
        if len(words) < 40 or len(sentences) < 3:
            raise ValueError(
                "There is not enough conceptual information in the provided notes to generate meaningful exam-style questions. "
                "Please provide longer or more detailed study material."
            )
            
        # Extract concepts
        concepts = self.concept_extractor.extract_concepts(text)
        
        # If no concepts are extracted, try to create basic sentence-based definition concepts
        if not concepts:
            if len(sentences) < 4:
                raise ValueError(
                    "The provided study notes are too brief or simple to extract meaningful concepts. "
                    "Please upload more comprehensive notes to generate high-quality questions."
                )
            # Create synthetic concepts from sentences
            for i, sent in enumerate(sentences):
                # Simple split to guess subject and predicate
                parts = sent.split(None, 3)
                if len(parts) >= 3:
                    subject = " ".join(parts[:2])
                    predicate = sent[len(subject):].strip()
                    # Clean relation word at start
                    if predicate.lower().startswith(('is', 'was', 'are', 'were')):
                        predicate = predicate.split(None, 1)[-1]
                    if len(subject) > 3 and len(predicate) > 10:
                        concepts.append(Concept(
                            type='definition',
                            text=sent,
                            context=sent,
                            confidence=0.3,
                            subject=subject,
                            predicate=predicate
                        ))
                        
        if not concepts:
            raise ValueError(
                "The provided notes do not contain clear concepts, definitions, or processes to generate high-quality questions. "
                "Please provide more detailed study material."
            )
            
        # Sort concepts by difficulty preference
        # Easy: definition, abbreviation, example
        # Medium: process, advantage, disadvantage
        # Hard: application, comparison
        priority_map = {
            'easy': ['definition', 'abbreviation', 'example', 'application', 'process', 'comparison', 'advantage', 'disadvantage'],
            'medium': ['process', 'advantage', 'disadvantage', 'comparison', 'definition', 'abbreviation', 'example', 'application'],
            'hard': ['application', 'comparison', 'process', 'advantage', 'disadvantage', 'definition', 'abbreviation', 'example']
        }
        
        priorities = priority_map.get(difficulty.lower(), priority_map['medium'])
        
        # Group concepts by type
        concepts_by_type = {}
        for c in concepts:
            concepts_by_type.setdefault(c.type, []).append(c)
            
        # Select concepts to use
        selected_concepts = []
        for c_type in priorities:
            if c_type in concepts_by_type:
                selected_concepts.extend(concepts_by_type[c_type])
            if len(selected_concepts) >= num_questions:
                break
                
        # Trim or pad selected concepts
        selected_concepts = selected_concepts[:num_questions]
        if len(selected_concepts) < num_questions:
            # Pad with any remaining concepts not selected
            all_ids = {id(c) for c in selected_concepts}
            remaining = [c for c in concepts if id(c) not in all_ids]
            selected_concepts.extend(remaining[:num_questions - len(selected_concepts)])
            
        # Generate questions
        questions = []
        
        for i, concept in enumerate(selected_concepts):
            try:
                # 1. Try to generate a question using Flan-T5 with a clear concept instruction
                q_data = self._generate_llm_question(concept, text, difficulty)
                if q_data and self._is_valid_mcq(q_data):
                    questions.append(q_data)
                else:
                    # 2. Fallback to robust concept-based template generator
                    q_data = self._generate_concept_question(concept, concepts, sentences, difficulty)
                    questions.append(q_data)
            except Exception as e:
                logger.error(f"Failed to generate question {i}: {e}")
                # Safe fallback
                try:
                    q_data = self._generate_concept_question(concept, concepts, sentences, difficulty)
                    questions.append(q_data)
                except Exception as ex:
                    logger.error(f"Fallback generation also failed: {ex}")
                    
        return questions[:num_questions]
    
    def _is_valid_mcq(self, q: Dict) -> bool:
        """Validate MCQ quality constraints."""
        if not q or not isinstance(q, dict):
            return False
        if 'question' not in q or 'options' not in q or 'correct' not in q:
            return False
        if not isinstance(q['options'], dict) or len(q['options']) != 4:
            return False
        # Check correct letter
        if q['correct'] not in ['A', 'B', 'C', 'D']:
            return False
        # Check uniqueness of options
        vals = [v.strip().lower() for v in q['options'].values()]
        if len(set(vals)) != 4:
            return False
        # Check forbidden word matching patterns
        question_lower = q['question'].lower()
        forbidden_patterns = [
            "which word appears",
            "which sentence is present",
            "what is the third word",
            "fill the blank using the exact sentence",
            "what is the word mentioned",
            "which of these words",
            "what is the exact phrase"
        ]
        for pattern in forbidden_patterns:
            if pattern in question_lower:
                return False
        return True
        
    def _generate_llm_question(self, concept, full_text: str, difficulty: str) -> Optional[Dict]:
        """Attempt to generate a question using the LLM model."""
        if self.model is None or self.tokenizer is None:
            return None
            
        context = concept.context
        subject = concept.subject
        predicate = concept.predicate
        
        prompt = f"""Generate a multiple-choice question testing understanding, reasoning, or application of the concept '{subject}' ({predicate}).
Do NOT ask about exact wording, word order, or keyword presence.
Create 4 unique, plausible options (A, B, C, D) and specify the correct answer letter.

Text: {context}

Format your output exactly as:
Question: <conceptual question>
Option A: <option A>
Option B: <option B>
Option C: <option C>
Option D: <option D>
Correct: <A, B, C, or D>"""

        try:
            inputs = self.tokenizer(
                prompt,
                max_length=512,
                truncation=True,
                return_tensors='pt'
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=250,
                    num_beams=1,
                    do_sample=False,
                    early_stopping=True,
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Parse response
            q_match = re.search(r'Question:\s*(.+)', response, re.IGNORECASE)
            a_match = re.search(r'Option A:\s*(.+)', response, re.IGNORECASE)
            b_match = re.search(r'Option B:\s*(.+)', response, re.IGNORECASE)
            c_match = re.search(r'Option C:\s*(.+)', response, re.IGNORECASE)
            d_match = re.search(r'Option D:\s*(.+)', response, re.IGNORECASE)
            correct_match = re.search(r'Correct:\s*([A-D])', response, re.IGNORECASE)
            
            if q_match and a_match and b_match and c_match and d_match and correct_match:
                q_data = {
                    'question': q_match.group(1).strip(),
                    'options': {
                        'A': a_match.group(1).strip(),
                        'B': b_match.group(1).strip(),
                        'C': c_match.group(1).strip(),
                        'D': d_match.group(1).strip(),
                    },
                    'correct': correct_match.group(1).strip().upper(),
                    'difficulty': difficulty
                }
                return q_data
            
            # Try parsing as JSON if LLM outputted JSON despite prompt
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                q_data = json.loads(json_match.group())
                # Normalize keys
                if 'options' in q_data and isinstance(q_data['options'], list):
                    opts = q_data['options']
                    if len(opts) == 4:
                        q_data['options'] = {'A': opts[0], 'B': opts[1], 'C': opts[2], 'D': opts[3]}
                q_data['difficulty'] = difficulty
                return q_data
                
            return None
        except Exception as e:
            logger.warning(f"LLM question generation failed: {e}")
            return None
            
    def _generate_concept_question(self, concept, all_concepts, all_sentences, difficulty: str) -> Dict:
        """Fallback conceptual template generator."""
        subject = concept.subject
        predicate = concept.predicate
        c_type = concept.type
        
        # Clean subject: capitalize
        subject_display = subject.strip()
        # Clean predicate
        pred_clean = predicate.strip()
        if pred_clean and not pred_clean[0].isupper():
            pred_clean = pred_clean[0].upper() + pred_clean[1:]
        if pred_clean.endswith('.'):
            pred_clean = pred_clean[:-1]
            
        # Select template questions based on difficulty preference
        diff_lower = difficulty.lower()
        
        if diff_lower == 'hard':
            scenarios = [
                f"A system implements '{subject_display}'. Which of the following best analyzes the operational outcome of this implementation?",
                f"In a real-life scenario where '{subject_display}' is active, which of the following results would be expected?",
                f"What would occur if the processes governing '{subject_display}' were completely suspended?",
                f"Which of the following scenarios best illustrates the application of '{subject_display}'?"
            ]
            question_text = random.choice(scenarios)
        elif diff_lower == 'medium':
            reasoning = [
                f"Which statement best describes the mechanism or process of '{subject_display}'?",
                f"Why is '{subject_display}' considered a key factor or process, according to the notes?",
                f"Which of the following correctly describes how '{subject_display}' functions?",
                f"What is the relationship between '{subject_display}' and the surrounding environment?"
            ]
            question_text = random.choice(reasoning)
        else:
            easy_q = [
                f"Which of the following best defines the concept of '{subject_display}'?",
                f"What is the primary purpose of '{subject_display}'?",
                f"Based on the notes, what is '{subject_display}'?",
                f"Which statement is the most accurate definition of '{subject_display}'?"
            ]
            question_text = random.choice(easy_q)
            
        # Extract other predicates for distractors
        other_predicates = [c.predicate for c in all_concepts if c.subject.lower() != subject.lower()]
        other_sents = [s for s in all_sentences if subject.lower() not in s.lower() and len(s) > 20]
        
        options, correct_letter = self._generate_options(pred_clean, other_predicates, other_sents)
        
        return {
            'question': question_text,
            'options': options,
            'correct': correct_letter,
            'difficulty': difficulty
        }
        
    def _generate_options(self, correct_val: str, other_predicates: List[str], other_sentences: List[str]) -> Tuple[Dict[str, str], str]:
        """Generate exactly 4 unique options with plausible distractors."""
        options_list = [correct_val]
        
        # 1. Grab predicates from other concepts
        for pred in other_predicates:
            if len(options_list) >= 4:
                break
            p_clean = pred.strip()
            if p_clean.endswith('.'):
                p_clean = p_clean[:-1]
            if p_clean and not p_clean[0].isupper():
                p_clean = p_clean[0].upper() + p_clean[1:]
                
            if p_clean.lower() not in [o.lower() for o in options_list]:
                options_list.append(p_clean)
                
        # 2. Grab other sentences
        for sent in other_sentences:
            if len(options_list) >= 4:
                break
            s_clean = sent.strip()
            if s_clean.endswith('.'):
                s_clean = s_clean[:-1]
            if s_clean and not s_clean[0].isupper():
                s_clean = s_clean[0].upper() + s_clean[1:]
                
            if len(s_clean) > 15 and s_clean.lower() not in [o.lower() for o in options_list]:
                options_list.append(s_clean)
                
        # 3. Create mutated options
        mutations = [
            lambda s: s.replace("is ", "is not ").replace("can ", "cannot ").replace("does ", "does not ").replace("increases", "decreases").replace("allows", "prevents").replace("absorb", "repel"),
            lambda s: "It primarily prevents the " + s[3:] if s.lower().startswith("it ") else "It prevents " + s,
            lambda s: "It has no significant effect on the " + s[3:] if s.lower().startswith("it ") else "It has no effect on " + s,
            lambda s: "It occurs only under extreme external pressure and " + s[3:] if s.lower().startswith("it ") else "It occurs under extreme conditions and " + s,
        ]
        for mutate in mutations:
            if len(options_list) >= 4:
                break
            mutated = mutate(correct_val)
            if mutated.lower() not in [o.lower() for o in options_list]:
                options_list.append(mutated)
                
        # 4. Add general placeholders
        generics = [
            "It represents a static state with no active energy transfer.",
            "It describes a mechanism that occurs only in artificial vacuum environments.",
            "It refers to the initial phase of system configuration.",
            "It is a theoretical concept with no practical application."
        ]
        for gen in generics:
            if len(options_list) >= 4:
                break
            if gen.lower() not in [o.lower() for o in options_list]:
                options_list.append(gen)
                
        # Shuffle options
        random.shuffle(options_list)
        
        mapping = {
            'A': options_list[0],
            'B': options_list[1],
            'C': options_list[2],
            'D': options_list[3]
        }
        correct_letter = [k for k, v in mapping.items() if v == correct_val][0]
        return mapping, correct_letter

    def validate_question(self, question: Dict, source_text: str) -> bool:
        """Validate that the question is answerable from the source text."""
        # This can be kept as a standard utility
        correct_answer = question['options'][question['correct']]
        if correct_answer.lower() in source_text.lower():
            return True
        return False
