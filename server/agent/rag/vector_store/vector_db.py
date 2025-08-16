"""
Vector Database for Government Scheme Content

Stores and manages vector embeddings for efficient similarity search.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import chromadb
from chromadb.config import Settings
import json
from pathlib import Path
from datetime import datetime
from ..vector_store.embeddings_manager import EmbeddingResult

class VectorDatabase:
    """Vector database for storing and querying government scheme embeddings"""
    
    def __init__(self, db_path: str = "./chroma_db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = Path(db_path)
        self.db_path.mkdir(exist_ok=True)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create collections for different types of content
        self.collections = {
            'govt_schemes': self._get_or_create_collection('govt_schemes'),
            'state_schemes': self._get_or_create_collection('state_schemes'),
            'central_schemes': self._get_or_create_collection('central_schemes'),
            'pdfs': self._get_or_create_collection('govt_pdfs')
        }
        
        self.logger.info("Vector database initialized successfully")
    
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection"""
        try:
            return self.client.get_collection(name)
        except Exception:
            return self.client.create_collection(
                name=name,
                metadata={"description": f"Government agricultural schemes - {name}"}
            )
    
    def store_embeddings(self, embedding_results: List[EmbeddingResult]) -> bool:
        """Store embeddings in the vector database"""
        try:
            self.logger.info(f"Storing {len(embedding_results)} embeddings...")
            
            # Group embeddings by collection type
            grouped_embeddings = self._group_embeddings_by_type(embedding_results)
            
            for collection_name, embeddings in grouped_embeddings.items():
                if not embeddings:
                    continue
                
                collection = self.collections[collection_name]
                
                # Prepare data for ChromaDB
                ids = [emb.content_id for emb in embeddings]
                embeddings_array = [emb.embedding.tolist() for emb in embeddings]
                documents = [emb.chunk_text for emb in embeddings]
                metadatas = [self._prepare_metadata(emb.metadata) for emb in embeddings]
                
                # Store in batches to avoid memory issues
                batch_size = 1000
                for i in range(0, len(ids), batch_size):
                    batch_ids = ids[i:i+batch_size]
                    batch_embeddings = embeddings_array[i:i+batch_size]
                    batch_documents = documents[i:i+batch_size]
                    batch_metadatas = metadatas[i:i+batch_size]
                    
                    # Upsert (insert or update)
                    collection.upsert(
                        ids=batch_ids,
                        embeddings=batch_embeddings,
                        documents=batch_documents,
                        metadatas=batch_metadatas
                    )
                
                self.logger.info(f"Stored {len(embeddings)} embeddings in {collection_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing embeddings: {e}")
            return False
    
    def _group_embeddings_by_type(self, embedding_results: List[EmbeddingResult]) -> Dict[str, List[EmbeddingResult]]:
        """Group embeddings by collection type"""
        grouped = {
            'govt_schemes': [],
            'state_schemes': [],
            'central_schemes': [],
            'pdfs': []
        }
        
        for emb in embedding_results:
            metadata = emb.metadata
            source_type = metadata.get('source_type', 'website')
            category = metadata.get('category', 'unknown')
            
            if source_type == 'pdf':
                grouped['pdfs'].append(emb)
            elif category == 'state':
                grouped['state_schemes'].append(emb)
            elif category == 'central':
                grouped['central_schemes'].append(emb)
            else:
                grouped['govt_schemes'].append(emb)
        
        return grouped
    
    def _prepare_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare metadata for ChromaDB storage"""
        # ChromaDB requires specific data types
        clean_metadata = {}
        
        for key, value in metadata.items():
            if value is None:
                continue
            elif isinstance(value, (str, int, float, bool)):
                clean_metadata[key] = value
            elif isinstance(value, list):
                clean_metadata[key] = json.dumps(value)
            elif isinstance(value, dict):
                clean_metadata[key] = json.dumps(value)
            else:
                clean_metadata[key] = str(value)
        
        # Add timestamp
        clean_metadata['indexed_at'] = datetime.now().isoformat()
        
        return clean_metadata
    
    def search_similar(self, query_embedding: np.ndarray, top_k: int = 10, 
                      filters: Optional[Dict[str, Any]] = None, 
                      collection_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for similar content using vector similarity"""
        try:
            collections_to_search = collection_names or list(self.collections.keys())
            all_results = []
            
            for collection_name in collections_to_search:
                if collection_name not in self.collections:
                    continue
                
                collection = self.collections[collection_name]
                
                # Prepare ChromaDB query
                where_clause = self._build_where_clause(filters) if filters else None
                
                results = collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=top_k,
                    where=where_clause,
                    include=['documents', 'metadatas', 'distances']
                )
                
                # Process results
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    
                    # Convert distance to similarity score
                    similarity = 1.0 / (1.0 + distance)
                    
                    all_results.append({
                        'content': doc,
                        'metadata': self._parse_metadata(metadata),
                        'similarity': similarity,
                        'collection': collection_name
                    })
            
            # Sort by similarity and return top results
            all_results.sort(key=lambda x: x['similarity'], reverse=True)
            return all_results[:top_k]
            
        except Exception as e:
            self.logger.error(f"Error searching similar content: {e}")
            return []
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build ChromaDB where clause from filters"""
        where_clause = {}
        
        for key, value in filters.items():
            if isinstance(value, list):
                where_clause[key] = {"$in": value}
            else:
                where_clause[key] = {"$eq": value}
        
        return where_clause
    
    def _parse_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse metadata from ChromaDB storage format"""
        parsed = {}
        
        for key, value in metadata.items():
            if isinstance(value, str) and value.startswith('[') or value.startswith('{'):
                try:
                    parsed[key] = json.loads(value)
                except json.JSONDecodeError:
                    parsed[key] = value
            else:
                parsed[key] = value
        
        return parsed
    
    def search_by_scheme_name(self, scheme_name: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for content by scheme name"""
        filters = {"scheme_name": {"$like": f"%{scheme_name}%"}}
        return self.search_similar(
            query_embedding=np.random.random(384),  # Placeholder, will use text search
            top_k=top_k,
            filters=filters
        )
    
    def search_by_state(self, state: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for state-specific schemes"""
        filters = {"state": state}
        return self.search_similar(
            query_embedding=np.random.random(384),  # Placeholder
            top_k=top_k,
            filters=filters,
            collection_names=['state_schemes', 'govt_schemes']
        )
    
    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about stored content"""
        stats = {}
        
        for name, collection in self.collections.items():
            try:
                count = collection.count()
                stats[name] = count
            except Exception as e:
                self.logger.warning(f"Error getting stats for {name}: {e}")
                stats[name] = 0
        
        return stats
    
    def delete_old_content(self, days_old: int = 30) -> bool:
        """Delete content older than specified days"""
        try:
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            
            for collection in self.collections.values():
                # This would require custom implementation based on your needs
                # ChromaDB doesn't have built-in date-based deletion
                pass
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting old content: {e}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the vector database"""
        try:
            import shutil
            backup_path = Path(backup_path)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Copy the entire ChromaDB directory
            shutil.copytree(self.db_path, backup_path / "chroma_backup", dirs_exist_ok=True)
            
            self.logger.info(f"Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return False
