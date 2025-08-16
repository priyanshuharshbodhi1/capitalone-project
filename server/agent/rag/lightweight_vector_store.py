"""
Lightweight Vector Store using SQLite FTS and TF-IDF

Replaces ChromaDB and sentence-transformers with a lightweight solution.
"""

import sqlite3
import json
import logging
import math
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from collections import Counter, defaultdict
import re
from datetime import datetime

class LightweightVectorStore:
    """Lightweight vector store using SQLite FTS and TF-IDF similarity"""
    
    def __init__(self, db_path: str = "./lightweight_rag.db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Initialize SQLite database with FTS
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Create tables
        self._create_tables()
        
        # TF-IDF cache
        self.tfidf_cache = {}
        self.document_frequencies = defaultdict(int)
        self.total_documents = 0
        
        self.logger.info("Lightweight vector store initialized")
    
    def _create_tables(self):
        """Create database tables"""
        cursor = self.conn.cursor()
        
        # Main documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                metadata TEXT,
                collection_type TEXT,
                created_at TEXT
            )
        ''')
        
        # FTS virtual table for fast text search
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                id,
                title,
                content,
                tokenize='porter'
            )
        ''')
        
        # Schemes table for structured data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schemes (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                eligibility TEXT,
                benefits TEXT,
                subsidy_amount TEXT,
                application_links TEXT,
                state TEXT,
                category TEXT,
                status TEXT,
                metadata TEXT,
                created_at TEXT
            )
        ''')
        
        self.conn.commit()
    
    def store_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Store documents in the lightweight vector store"""
        try:
            cursor = self.conn.cursor()
            
            for doc in documents:
                doc_id = doc.get('id', f"doc_{hash(doc.get('content', ''))}")
                title = doc.get('title', '')
                content = doc.get('content', '')
                metadata = json.dumps(doc.get('metadata', {}))
                collection_type = doc.get('collection_type', 'general')
                created_at = datetime.now().isoformat()
                
                # Insert into main table
                cursor.execute('''
                    INSERT OR REPLACE INTO documents 
                    (id, title, content, metadata, collection_type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (doc_id, title, content, metadata, collection_type, created_at))
                
                # Insert into FTS table
                cursor.execute('''
                    INSERT OR REPLACE INTO documents_fts 
                    (id, title, content)
                    VALUES (?, ?, ?)
                ''', (doc_id, title, content))
            
            self.conn.commit()
            
            # Update TF-IDF cache
            self._update_tfidf_cache()
            
            self.logger.info(f"Stored {len(documents)} documents")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing documents: {e}")
            return False
    
    def store_scheme(self, scheme_data: Dict[str, Any]) -> bool:
        """Store structured scheme data"""
        try:
            cursor = self.conn.cursor()
            
            scheme_id = scheme_data.get('id', f"scheme_{hash(scheme_data.get('name', ''))}")
            
            cursor.execute('''
                INSERT OR REPLACE INTO schemes 
                (id, name, description, eligibility, benefits, subsidy_amount, 
                 application_links, state, category, status, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                scheme_id,
                scheme_data.get('name', ''),
                scheme_data.get('description', ''),
                json.dumps(scheme_data.get('eligibility', [])),
                json.dumps(scheme_data.get('benefits', [])),
                scheme_data.get('subsidy_amount', ''),
                json.dumps(scheme_data.get('application_links', [])),
                scheme_data.get('state', ''),
                scheme_data.get('category', ''),
                scheme_data.get('status', 'active'),
                json.dumps(scheme_data.get('metadata', {})),
                datetime.now().isoformat()
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing scheme: {e}")
            return False
    
    def search_similar(self, query: str, top_k: int = 10, 
                      filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents using FTS and TF-IDF"""
        try:
            results = []
            
            # FTS search
            fts_results = self._fts_search(query, top_k * 2, filters)
            
            # Calculate TF-IDF similarity for ranking
            query_terms = self._tokenize(query.lower())
            
            for doc in fts_results:
                similarity = self._calculate_tfidf_similarity(query_terms, doc['content'])
                
                results.append({
                    'content': doc['content'],
                    'metadata': json.loads(doc.get('metadata', '{}')),
                    'similarity': similarity,
                    'title': doc.get('title', ''),
                    'collection': doc.get('collection_type', 'general')
                })
            
            # Sort by similarity and return top results
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            self.logger.error(f"Error in similarity search: {e}")
            return []
    
    def search_schemes(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search structured schemes"""
        try:
            cursor = self.conn.cursor()
            
            # Build SQL query
            sql = "SELECT * FROM schemes WHERE 1=1"
            params = []
            
            # Add search conditions
            if query:
                sql += " AND (name LIKE ? OR description LIKE ?)"
                query_pattern = f"%{query}%"
                params.extend([query_pattern, query_pattern])
            
            # Add filters
            if filters:
                if filters.get('state'):
                    sql += " AND state = ?"
                    params.append(filters['state'])
                
                if filters.get('category'):
                    sql += " AND category = ?"
                    params.append(filters['category'])
                
                if filters.get('status'):
                    sql += " AND status = ?"
                    params.append(filters['status'])
            
            sql += " ORDER BY created_at DESC LIMIT 20"
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'scheme_id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'eligibility': json.loads(row['eligibility'] or '[]'),
                    'benefits': json.loads(row['benefits'] or '[]'),
                    'subsidy_amount': row['subsidy_amount'],
                    'application_links': json.loads(row['application_links'] or '[]'),
                    'state': row['state'],
                    'category': row['category'],
                    'status': row['status'],
                    'metadata': json.loads(row['metadata'] or '{}'),
                    'relevance_score': self._calculate_text_relevance(query, row['name'], row['description'])
                })
            
            # Sort by relevance
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching schemes: {e}")
            return []
    
    def _fts_search(self, query: str, limit: int, filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Full-text search using SQLite FTS"""
        cursor = self.conn.cursor()
        
        # Prepare FTS query
        fts_query = self._prepare_fts_query(query)
        
        # Execute FTS search
        cursor.execute('''
            SELECT d.*, df.rank
            FROM documents_fts df
            JOIN documents d ON d.id = df.id
            WHERE documents_fts MATCH ?
            ORDER BY df.rank
            LIMIT ?
        ''', (fts_query, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _prepare_fts_query(self, query: str) -> str:
        """Prepare query for FTS"""
        # Clean and prepare query terms
        terms = re.findall(r'\w+', query.lower())
        
        # Add wildcards for partial matching
        fts_terms = [f'"{term}"*' for term in terms if len(term) > 2]
        
        if not fts_terms:
            return query
        
        return ' OR '.join(fts_terms)
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        # Remove punctuation and split
        words = re.findall(r'\w+', text.lower())
        
        # Remove common stop words
        stop_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of'}
        return [word for word in words if word not in stop_words and len(word) > 2]
    
    def _calculate_tfidf_similarity(self, query_terms: List[str], document_content: str) -> float:
        """Calculate TF-IDF similarity between query and document"""
        doc_terms = self._tokenize(document_content)
        doc_term_counts = Counter(doc_terms)
        
        score = 0.0
        
        for term in query_terms:
            if term in doc_term_counts:
                # Term frequency in document
                tf = doc_term_counts[term] / len(doc_terms) if doc_terms else 0
                
                # Inverse document frequency (simplified)
                idf = math.log(self.total_documents / (self.document_frequencies.get(term, 1) + 1))
                
                # TF-IDF score
                score += tf * idf
        
        # Normalize by query length
        return score / len(query_terms) if query_terms else 0
    
    def _calculate_text_relevance(self, query: str, title: str, description: str) -> float:
        """Calculate text relevance score"""
        query_lower = query.lower()
        score = 0.0
        
        # Exact matches get higher scores
        if query_lower in title.lower():
            score += 2.0
        
        if query_lower in description.lower():
            score += 1.5
        
        # Word-level matches
        query_words = query_lower.split()
        title_lower = title.lower()
        description_lower = description.lower()
        
        for word in query_words:
            if word in title_lower:
                score += 0.5
            if word in description_lower:
                score += 0.3
        
        return score
    
    def _update_tfidf_cache(self):
        """Update TF-IDF document frequencies"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        self.total_documents = cursor.fetchone()[0]
        
        # Update document frequencies
        cursor.execute("SELECT content FROM documents")
        self.document_frequencies.clear()
        
        for (content,) in cursor.fetchall():
            terms = set(self._tokenize(content))
            for term in terms:
                self.document_frequencies[term] += 1
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM schemes")
        scheme_count = cursor.fetchone()[0]
        
        return {
            'total_documents': doc_count,
            'total_schemes': scheme_count
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
