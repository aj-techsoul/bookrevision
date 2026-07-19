from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import logging
from typing import Dict, List, Optional
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGChatbot:
    """Retrieval-Augmented Generation chatbot for document Q&A."""
    
    def __init__(self, 
                 embedding_model,
                 vector_db,
                 llm_model_name: str = 'google/flan-t5-large'):
        """
        Initialize RAG chatbot.
        
        Args:
            embedding_model: EmbeddingModel instance
            vector_db: VectorDatabase instance
            llm_model_name: LLM model for answer generation
        """
        self.embedding_model = embedding_model
        self.vector_db = vector_db
        self.llm_model_name = llm_model_name
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        self.tokenizer = None
        self.model = None
        self._load_llm()
    
    def _load_llm(self):
        """Load the language model for answer generation."""
        logger.info(f"Loading LLM: {self.llm_model_name}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.llm_model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.llm_model_name)
        self.model.to(self.device)
        self.model.eval()  # Set to evaluation mode for faster inference
        
        logger.info("LLM loaded")
    
    def answer_question(self, 
                       question: str, 
                       k: int = 4,
                       confidence_threshold: float = 0.3) -> Dict:
        """
        Answer a question using RAG.
        
        Args:
            question: User's question
            k: Number of chunks to retrieve
            confidence_threshold: Minimum similarity threshold
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        # Embed the question
        question_embedding = self.embedding_model.embed_text(question)
        
        # Retrieve relevant chunks
        retrieved_chunks = self.vector_db.search(question_embedding, k=k)
        
        # Filter by confidence threshold
        relevant_chunks = [
            chunk for chunk in retrieved_chunks 
            if chunk['similarity'] >= confidence_threshold
        ]
        
        if not relevant_chunks:
            context = "No relevant context found in the uploaded documents."
            avg_similarity = 0.0
        else:
            # Build context from retrieved chunks
            context = self._build_context(relevant_chunks)
            avg_similarity = np.mean([chunk['similarity'] for chunk in relevant_chunks])
        
        # Generate answer
        answer = self._generate_answer(question, context)
        
        return {
            'answer': answer,
            'sources': [
                {
                    'chunk_id': chunk['chunk_index'],
                    'text': chunk['text'][:200] + '...' if len(chunk['text']) > 200 else chunk['text'],
                    'similarity': chunk['similarity']
                }
                for chunk in relevant_chunks
            ],
            'confidence': float(avg_similarity),
            'found': True
        }
    
    def _build_context(self, chunks: List[dict]) -> str:
        """Build context string from retrieved_CHUNKS."""
        context_parts = []
        for i, chunk in enumerate(chunks):
            context_parts.append(f"[Source {i+1}]: {chunk['text']}")
        
        return '\n\n'.join(context_parts)
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using LLM with context."""
        prompt = f"""You are a helpful AI study assistant. Answer the following question. Use the provided context from the user's notes if it is relevant. If the context does not contain the answer, use your general knowledge to answer, but kindly mention that it is not from the notes.

Context:
{context}

Question: {question}

Answer:"""
        
        try:
            inputs = self.tokenizer(
                prompt,
                max_length=1024,
                truncation=True,
                return_tensors='pt'
            ).to(self.device)
            
            outputs = self.model.generate(
                inputs.input_ids,
                max_length=300,
                min_length=20,
                do_sample=False
            )
            
            answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return answer.strip()
            
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return "I encountered an error while generating the answer."
    
    def chat(self, 
            message: str, 
            conversation_history: List[Dict] = None) -> Dict:
        """
        Chat with conversation history support.
        
        Args:
            message: Current user message
            conversation_history: List of previous conversation turns
            
        Returns:
            Response with answer and metadata
        """
        if conversation_history is None:
            conversation_history = []
        
        # For now, just answer the current message
        # In a more advanced version, we would incorporate conversation history
        return self.answer_question(message)
