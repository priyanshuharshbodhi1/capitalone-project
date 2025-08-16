"""
Lightweight RAG Agent for Government Agricultural Schemes

Replaces LangGraph with a simple state machine and workflow.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

from .lightweight_vector_store import LightweightVectorStore
from .indexer.govt_website_indexer import GovtWebsiteIndexer
from .indexer.pdf_processor import PDFProcessor

class LightweightRAGAgent:
    """Lightweight RAG agent without heavy dependencies"""
    
    def __init__(self, 
                 db_path: str = "./lightweight_rag.db"):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.vector_store = LightweightVectorStore(db_path=db_path)
        self.website_indexer = GovtWebsiteIndexer()
        self.pdf_processor = PDFProcessor()
        
        self.logger.info("Lightweight RAG Agent initialized")
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a government scheme query using lightweight RAG"""
        try:
            self.logger.info(f"Processing query: {query}")
            
            # Step 1: Analyze query
            query_analysis = self._analyze_query(query, context)
            
            # Step 2: Search vector store
            documents = self._search_documents(query, query_analysis)
            
            # Step 3: Search structured schemes
            schemes = self._search_schemes(query, query_analysis)
            
            # Step 4: Synthesize results
            response = self._synthesize_response(query, documents, schemes, query_analysis)
            
            self.logger.info(f"Query processed successfully")
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return {
                "success": False,
                "error": f"Failed to process query: {str(e)}",
                "query": query
            }
    
    def _analyze_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the user query to extract intent and parameters"""
        query_lower = query.lower()
        
        # Extract farmer type
        farmer_type = None
        if context and context.get('farmer_type'):
            farmer_type = context['farmer_type']
        elif any(term in query_lower for term in ["small farmer", "marginal farmer"]):
            farmer_type = "small/marginal"
        elif "large farmer" in query_lower:
            farmer_type = "large"
        else:
            farmer_type = "all"
        
        # Extract state information
        target_state = None
        if context and context.get('location', {}).get('state'):
            target_state = context['location']['state']
        else:
            # Simple state detection
            indian_states = [
                "andhra pradesh", "assam", "bihar", "gujarat", "haryana", 
                "karnataka", "kerala", "madhya pradesh", "maharashtra", 
                "odisha", "punjab", "rajasthan", "tamil nadu", "telangana",
                "uttar pradesh", "west bengal"
            ]
            
            for state in indian_states:
                if state in query_lower:
                    target_state = state
                    break
        
        # Extract category/intent
        category = "general"
        if any(term in query_lower for term in ["irrigation", "drip", "water", "micro irrigation"]):
            category = "irrigation"
        elif any(term in query_lower for term in ["seed", "seeds"]):
            category = "seeds"
        elif any(term in query_lower for term in ["fertilizer", "fertiliser"]):
            category = "fertilizers"
        elif any(term in query_lower for term in ["insurance", "crop insurance"]):
            category = "insurance"
        elif any(term in query_lower for term in ["subsidy", "subsidies"]):
            category = "subsidy"
        
        return {
            "farmer_type": farmer_type,
            "target_state": target_state,
            "category": category,
            "query_intent": self._detect_intent(query_lower)
        }
    
    def _detect_intent(self, query_lower: str) -> str:
        """Detect the intent of the query"""
        if any(term in query_lower for term in ["how to apply", "application", "apply"]):
            return "application_process"
        elif any(term in query_lower for term in ["eligibility", "eligible", "qualify"]):
            return "eligibility_check"
        elif any(term in query_lower for term in ["amount", "money", "subsidy", "benefit"]):
            return "benefit_inquiry"
        elif any(term in query_lower for term in ["document", "documents", "papers"]):
            return "documentation"
        else:
            return "general_inquiry"
    
    def _search_documents(self, query: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        filters = {}
        
        if analysis.get('target_state'):
            filters['state'] = analysis['target_state']
        
        if analysis.get('category') and analysis['category'] != 'general':
            filters['category'] = analysis['category']
        
        return self.vector_store.search_similar(query, top_k=10, filters=filters)
    
    def _search_schemes(self, query: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for relevant schemes in structured data"""
        filters = {}
        
        if analysis.get('target_state'):
            filters['state'] = analysis['target_state']
        
        if analysis.get('category') and analysis['category'] != 'general':
            filters['category'] = analysis['category']
        
        # Always search for active schemes
        filters['status'] = 'active'
        
        return self.vector_store.search_schemes(query, filters=filters)
    
    def _synthesize_response(self, query: str, documents: List[Dict[str, Any]], 
                           schemes: List[Dict[str, Any]], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize response from search results"""
        
        # Combine and deduplicate results
        all_schemes = []
        
        # Process structured schemes (higher priority)
        for scheme in schemes[:5]:  # Top 5 schemes
            all_schemes.append({
                "name": scheme.get('name', 'Government Scheme'),
                "description": scheme.get('description', ''),
                "eligibility": scheme.get('eligibility', []),
                "benefits": scheme.get('benefits', []),
                "subsidy_amount": scheme.get('subsidy_amount', ''),
                "application_links": scheme.get('application_links', []),
                "state": scheme.get('state', ''),
                "category": scheme.get('category', 'general'),
                "status": scheme.get('status', 'active'),
                "relevance_score": scheme.get('relevance_score', 0.8),
                "data_source": "structured_schemes"
            })
        
        # Process document results
        scheme_names_added = set(scheme.get('name', '').lower() for scheme in all_schemes)
        
        for doc in documents[:5]:  # Top 5 documents
            metadata = doc.get('metadata', {})
            scheme_name = metadata.get('scheme_name', '').lower()
            
            # Avoid duplicates
            if scheme_name and scheme_name not in scheme_names_added:
                content = doc.get('content', '')
                
                all_schemes.append({
                    "name": metadata.get('scheme_name', 'Government Scheme'),
                    "description": content[:300] + "..." if len(content) > 300 else content,
                    "eligibility": self._extract_from_content(content, "eligibility"),
                    "benefits": self._extract_from_content(content, "benefits"),
                    "subsidy_amount": self._extract_subsidy_amount(content),
                    "application_links": [metadata.get('url', '')],
                    "state": metadata.get('state', ''),
                    "category": metadata.get('category', 'general'),
                    "status": "active",
                    "relevance_score": doc.get('similarity', 0.5),
                    "data_source": "documents"
                })
                
                scheme_names_added.add(scheme_name)
        
        # Calculate confidence
        if all_schemes:
            max_score = max(scheme.get("relevance_score", 0) for scheme in all_schemes)
            confidence = min(max_score * 0.9, 1.0)  # Cap at 90%
        else:
            confidence = 0.0
        
        # Generate response
        if not all_schemes:
            return {
                "success": False,
                "message": "No relevant government schemes found for your query.",
                "schemes": [],
                "confidence": 0.0,
                "suggestions": self._generate_suggestions(query, analysis)
            }
        
        return {
            "success": True,
            "message": f"Found {len(all_schemes)} relevant government schemes.",
            "schemes": all_schemes,
            "confidence": confidence,
            "total_found": len(all_schemes),
            "query_processed": query,
            "farmer_recommendations": self._generate_farmer_recommendations(all_schemes, analysis)
        }
    
    def _extract_from_content(self, content: str, info_type: str) -> List[str]:
        """Extract specific information from content"""
        content_lower = content.lower()
        
        if info_type == "eligibility":
            patterns = [
                r'eligibility[:\s]*([^.\n]+)',
                r'eligible[:\s]*([^.\n]+)',
                r'(?:small|marginal|large)\s+farmer[s]?'
            ]
        elif info_type == "benefits":
            patterns = [
                r'benefit[s]?[:\s]*([^.\n]+)',
                r'subsidy[:\s]*([^.\n]+)',
                r'₹[0-9,]+[^.\n]*'
            ]
        else:
            return []
        
        results = []
        for pattern in patterns:
            matches = re.findall(pattern, content_lower, re.I)
            results.extend([match.strip() for match in matches if match.strip()])
        
        return list(set(results))[:3]  # Return unique, limited list
    
    def _extract_subsidy_amount(self, content: str) -> str:
        """Extract subsidy amount from content"""
        patterns = [
            r'subsidy[:\s]*([^.\n]*(?:₹|rs|rupee)[^.\n]*)',
            r'(?:₹|rs\.?)\s*([0-9,]+(?:\.[0-9]+)?)[^.\n]*',
            r'([0-9]+%[^.\n]*subsidy)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.I)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _generate_suggestions(self, query: str, analysis: Dict[str, Any]) -> List[str]:
        """Generate suggestions when no results found"""
        suggestions = [
            "Try using more specific terms like 'PM-KISAN' or 'drip irrigation subsidy'",
            "Contact your local agricultural extension office for personalized guidance",
            "Visit the official PM-KISAN website: pmkisan.gov.in"
        ]
        
        if not analysis.get('target_state'):
            suggestions.insert(0, "Mention your state name for state-specific schemes")
        
        return suggestions
    
    def _generate_farmer_recommendations(self, schemes: List[Dict[str, Any]], 
                                       analysis: Dict[str, Any]) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        farmer_type = analysis.get('farmer_type', 'all')
        
        if farmer_type == "small/marginal":
            recommendations.append("As a small/marginal farmer, focus on schemes with higher subsidy rates")
            recommendations.append("Consider joining Farmer Producer Organizations (FPOs) for better benefits")
        
        if analysis.get('category') == 'irrigation':
            recommendations.append("Drip irrigation can save 30-50% water and increase yield significantly")
            recommendations.append("Apply for irrigation schemes before the monsoon season")
        
        recommendations.extend([
            "Keep all required documents (Aadhaar, land records, bank details) ready",
            "Visit your nearest Krishi Vigyan Kendra for technical guidance",
            "Apply within the specified deadlines to avoid rejection"
        ])
        
        return recommendations
    
    async def index_government_sources(self) -> Dict[str, Any]:
        """Index government sources (simplified version)"""
        try:
            self.logger.info("Starting government sources indexing...")
            
            # Index websites
            website_content = await self.website_indexer.start_indexing()
            
            # Convert to document format
            documents = []
            for content in website_content:
                documents.append({
                    'id': f"web_{hash(content.url)}",
                    'title': content.title,
                    'content': content.content,
                    'metadata': {
                        'url': content.url,
                        'scheme_name': content.scheme_name,
                        'state': content.state,
                        'category': content.category,
                        'source_type': 'website'
                    },
                    'collection_type': content.category
                })
                
                # Also store as structured scheme if detailed enough
                if content.scheme_name and content.eligibility:
                    self.vector_store.store_scheme({
                        'id': f"scheme_{hash(content.scheme_name)}",
                        'name': content.scheme_name,
                        'description': content.content[:500],
                        'eligibility': content.eligibility,
                        'benefits': [],
                        'subsidy_amount': content.subsidy_amount or '',
                        'application_links': [content.url],
                        'state': content.state,
                        'category': content.category,
                        'status': 'active'
                    })
            
            # Store documents
            if documents:
                self.vector_store.store_documents(documents)
            
            return {
                "success": True,
                "websites_indexed": len(website_content),
                "documents_stored": len(documents),
                "message": "Government sources indexed successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error indexing government sources: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return self.vector_store.get_stats()
    
    def close(self):
        """Close the agent"""
        self.vector_store.close()
