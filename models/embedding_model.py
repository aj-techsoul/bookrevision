from sentence_transformers import SentenceTransformer
import numpy as np
import logging
from typing import List, Union
import faiss
import pickle
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Handle text embeddings using sentence-transformers."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize embedding model.
        
        Args:
            model_name: Name of the sentence-transformer model
        """
        self.model_name = model_name
        self.model = None
        self.dimension = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model."""
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.dimension}")
    
    def embed_text(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for text(s).
        
        Args:
            text: Single text string or list of strings
            
        Returns:
            Numpy array of embeddings
        """
        if isinstance(text, str):
            text = [text]
        
        embeddings = self.model.encode(text, show_progress_bar=False)
        return embeddings
    
    def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        """
        Add embeddings to chunk dictionaries.
        
        Args:
            chunks: List of chunk dictionaries with 'text' key
            
        Returns:
            Chunks with added 'embedding' key
        """
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embed_text(texts)
        
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding
        
        return chunks


class VectorDatabase:
    """Handle vector database operations using FAISS."""
    
    def __init__(self, dimension: int = 384, index_type: str = 'flat'):
        """
        Initialize vector database.
        
        Args:
            dimension: Embedding dimension
            index_type: Type of FAISS index ('flat', 'ivf', 'hnsw')
        """
        self.dimension = dimension
        self.index_type = index_type
        self.index = None
        self.chunk_metadata = []
        self._create_index()
    
    def _create_index(self):
        """Create FAISS index."""
        if self.index_type == 'flat':
            # Exact search, most accurate
            self.index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == 'ivf':
            # Inverted file index, faster for large datasets
            quantizer = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
        elif self.index_type == 'hnsw':
            # Hierarchical navigable small world
            self.index = faiss.IndexHNSWFlat(self.dimension, 32)
        else:
            raise ValueError(f"Unknown index type: {self.index_type}")
        
        logger.info(f"Created FAISS index: {self.index_type}")
    
    def add_embeddings(self, embeddings, metadata: List[dict]):
        """
        Add embeddings to the index.
        
        Args:
            embeddings: Numpy array or list of embeddings
            metadata: List of metadata dictionaries for each embedding
        """
        # Convert list of arrays to a single 2D numpy array if needed
        if not isinstance(embeddings, np.ndarray):
            embeddings = np.array(embeddings)
        embeddings = embeddings.astype('float32')

        if self.index_type == 'ivf':
            # IVF index needs training
            if not self.index.is_trained:
                self.index.train(embeddings)
        
        self.index.add(embeddings)
        self.chunk_metadata.extend(metadata)
        logger.info(f"Added {len(embeddings)} embeddings to index")
    
    def search(self, 
               query_embedding: np.ndarray, 
               k: int = 5) -> List[dict]:
        """
        Search for similar chunks.
        
        Args:
            query_embedding: Embedding of query
            k: Number of results to return
            
        Returns:
            List of (chunk, distance) tuples
        """
        if isinstance(query_embedding, np.ndarray) and query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.chunk_metadata):
                result = self.chunk_metadata[idx].copy()
                result['distance'] = float(dist)
                result['similarity'] = 1 / (1 + float(dist))  # Convert to similarity
                results.append(result)
        
        return results
    
    def save(self, save_path: str):
        """
        Save index and metadata to disk.
        
        Args:
            save_path: Directory to save index
        """
        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path / 'index.faiss'))
        
        # Save metadata
        with open(save_path / 'metadata.pkl', 'wb') as f:
            pickle.dump(self.chunk_metadata, f)
        
        logger.info(f"Saved index to {save_path}")
    
    def load(self, load_path: str):
        """
        Load index and metadata from disk.
        
        Args:
            load_path: Directory to load index from
        """
        load_path = Path(load_path)
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path / 'index.faiss'))
        
        # Load metadata
        with open(load_path / 'metadata.pkl', 'rb') as f:
            self.chunk_metadata = pickle.load(f)
        
        logger.info(f"Loaded index from {load_path}")
    
    def get_stats(self) -> dict:
        """Get database statistics."""
        return {
            'total_chunks': len(self.chunk_metadata),
            'index_type': self.index_type,
            'dimension': self.dimension
        }
