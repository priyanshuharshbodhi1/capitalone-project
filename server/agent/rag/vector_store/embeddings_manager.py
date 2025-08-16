"""
Embeddings Manager for Government Scheme Content

Generates and manages embeddings for indexed government agricultural content.
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from dataclasses import dataclass
import hashlib
import pickle
import os
from pathlib import Path

@dataclass
class EmbeddingResult:
    content_id: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    chunk_text: str

class EmbeddingsManager:
    """Manage embeddings for government scheme content"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: str = "./embeddings_cache"):
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize the embedding model
        self.model = self._load_model()
        
        # Embedding cache for performance
        self.embedding_cache: Dict[str, np.ndarray] = {}
        self._load_cache()
    
    def _load_model(self) -> SentenceTransformer:
        """Load the sentence transformer model"""
        try:
            self.logger.info(f"Loading embedding model: {self.model_name}")
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            model = SentenceTransformer(self.model_name, device=device)
            self.logger.info(f"Model loaded successfully on {device}")
            return model
        except Exception as e:
            self.logger.error(f"Failed to load model {self.model_name}: {e}")
            # Fallback to a smaller model
            self.model_name = "all-MiniLM-L6-v2"
            return SentenceTransformer(self.model_name)
    
    def generate_embeddings(self, content_list: List[Dict[str, Any]]) -> List[EmbeddingResult]:
        """Generate embeddings for a list of content items"""
        self.logger.info(f"Generating embeddings for {len(content_list)} content items...")
        
        embedding_results = []
        
        for content in content_list:
            try:
                # Create chunks from content
                chunks = self._create_content_chunks(content)
                
                for chunk in chunks:
                    # Generate content ID
                    content_id = self._generate_content_id(chunk['text'], content.get('url', ''))
                    
                    # Check cache first
                    if content_id in self.embedding_cache:
                        embedding = self.embedding_cache[content_id]
                    else:
                        # Generate new embedding
                        embedding = self._generate_single_embedding(chunk['text'])
                        self.embedding_cache[content_id] = embedding
                    
                    embedding_results.append(EmbeddingResult(
                        content_id=content_id,
                        embedding=embedding,
                        metadata={
                            'url': content.get('url', ''),
                            'title': content.get('title', ''),
                            'scheme_name': content.get('scheme_name', ''),
                            'state': content.get('state', ''),
                            'category': content.get('category', ''),
                            'chunk_index': chunk['index'],
                            'total_chunks': len(chunks),
                            'source_type': content.get('source_type', 'website')
                        },
                        chunk_text=chunk['text']
                    ))
                    
            except Exception as e:
                self.logger.error(f"Error generating embedding for content: {e}")
                continue
        
        # Save cache
        self._save_cache()
        
        self.logger.info(f"Generated {len(embedding_results)} embeddings successfully")
        return embedding_results
    
    def _create_content_chunks(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split content into chunks for better embedding quality"""
        text = content.get('content', '')
        if not text:
            return []
        
        # Chunk size optimized for government scheme content
        chunk_size = 512
        overlap = 50
        
        # Split by sentences first
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append({
                    'text': current_chunk.strip(),
                    'index': chunk_index
                })
                
                # Create overlap by keeping last few words
                words = current_chunk.split()
                overlap_words = words[-overlap:] if len(words) > overlap else words
                current_chunk = ' '.join(overlap_words) + ' ' + sentence
                chunk_index += 1
            else:
                current_chunk += ' ' + sentence
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'index': chunk_index
            })
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        import re
        
        # Simple sentence splitting for government documents
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    def _generate_single_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        try:
            # Preprocess text for government schemes
            processed_text = self._preprocess_text(text)
            
            # Generate embedding
            embedding = self.model.encode(processed_text, convert_to_numpy=True)
            
            # Normalize embedding
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(self.model.get_sentence_embedding_dimension())
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better embedding quality"""
        import re
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Expand common government abbreviations
        abbreviations = {
            'GoI': 'Government of India',
            'MoA': 'Ministry of Agriculture',
            'PM': 'Prime Minister',
            'CM': 'Chief Minister',
            'FPO': 'Farmer Producer Organization',
            'SHG': 'Self Help Group',
            'PMKSY': 'Pradhan Mantri Krishi Sinchayee Yojana',
            'PMFBY': 'Pradhan Mantri Fasal Bima Yojana',
            'PKVY': 'Paramparagat Krishi Vikas Yojana'
        }
        
        for abbr, full_form in abbreviations.items():
            text = re.sub(rf'\b{abbr}\b', full_form, text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _generate_content_id(self, text: str, url: str) -> str:
        """Generate unique ID for content"""
        content_hash = hashlib.md5(f"{text[:100]}{url}".encode()).hexdigest()
        return f"govt_scheme_{content_hash}"
    
    def _load_cache(self):
        """Load embedding cache from disk"""
        cache_file = self.cache_dir / "embeddings_cache.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    self.embedding_cache = pickle.load(f)
                self.logger.info(f"Loaded {len(self.embedding_cache)} cached embeddings")
            except Exception as e:
                self.logger.warning(f"Failed to load embedding cache: {e}")
                self.embedding_cache = {}
    
    def _save_cache(self):
        """Save embedding cache to disk"""
        cache_file = self.cache_dir / "embeddings_cache.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(self.embedding_cache, f)
            self.logger.info(f"Saved {len(self.embedding_cache)} embeddings to cache")
        except Exception as e:
            self.logger.warning(f"Failed to save embedding cache: {e}")
    
    def compute_similarity(self, query_embedding: np.ndarray, content_embeddings: List[np.ndarray]) -> List[float]:
        """Compute cosine similarity between query and content embeddings"""
        similarities = []
        
        for content_embedding in content_embeddings:
            # Cosine similarity
            similarity = np.dot(query_embedding, content_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(content_embedding)
            )
            similarities.append(float(similarity))
        
        return similarities
    
    def get_query_embedding(self, query: str) -> np.ndarray:
        """Generate embedding for a search query"""
        # Enhance query with agricultural context
        enhanced_query = self._enhance_query(query)
        return self._generate_single_embedding(enhanced_query)
    
    def _enhance_query(self, query: str) -> str:
        """Enhance search query with agricultural context"""
        # Add relevant context terms for better retrieval
        context_terms = [
            "agricultural scheme", "farmer subsidy", "government policy",
            "agricultural benefit", "rural development", "farming assistance"
        ]
        
        # Add context if query is short
        if len(query.split()) < 3:
            return f"{query} {' '.join(context_terms[:2])}"
        
        return query
