"""
LangGraph-based RAG Agent for Government Agricultural Schemes

Uses LangGraph to orchestrate retrieval and generation for government policy queries.
"""

import logging
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator
from datetime import datetime

from .vector_store.vector_db import VectorDatabase
from .vector_store.embeddings_manager import EmbeddingsManager
from .knowledge_base.govt_schemes_kb import GovtSchemesKB

class RAGState(TypedDict):
    """State for the RAG workflow"""
    query: str
    user_location: Optional[Dict[str, Any]]
    farmer_type: Optional[str]
    retrieved_documents: List[Dict[str, Any]]
    knowledge_base_results: List[Dict[str, Any]]
    final_response: Dict[str, Any]
    confidence_score: float
    processing_steps: Annotated[List[str], operator.add]

class LangGraphRAGAgent:
    """LangGraph-based RAG agent for government scheme queries"""
    
    def __init__(self, 
                 vector_db_path: str = "./chroma_db",
                 embeddings_cache_dir: str = "./embeddings_cache",
                 kb_path: str = "./schemes_kb"):
        self.logger = logging.getLogger(__name__)
        
        # Initialize RAG components
        self.vector_db = VectorDatabase(db_path=vector_db_path)
        self.embeddings_manager = EmbeddingsManager(cache_dir=embeddings_cache_dir)
        self.knowledge_base = GovtSchemesKB(kb_path=kb_path)
        
        # Build the LangGraph workflow
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
        
        self.logger.info("LangGraph RAG Agent initialized successfully")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for RAG"""
        workflow = StateGraph(RAGState)
        
        # Add nodes
        workflow.add_node("query_analysis", self._analyze_query)
        workflow.add_node("vector_retrieval", self._retrieve_from_vector_db)
        workflow.add_node("knowledge_base_search", self._search_knowledge_base)
        workflow.add_node("result_synthesis", self._synthesize_results)
        workflow.add_node("response_generation", self._generate_response)
        
        # Define the workflow edges
        workflow.set_entry_point("query_analysis")
        workflow.add_edge("query_analysis", "vector_retrieval")
        workflow.add_edge("vector_retrieval", "knowledge_base_search")
        workflow.add_edge("knowledge_base_search", "result_synthesis")
        workflow.add_edge("result_synthesis", "response_generation")
        workflow.add_edge("response_generation", END)
        
        return workflow
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a government scheme query using RAG"""
        try:
            self.logger.info(f"Processing query: {query}")
            
            # Initialize state
            initial_state = RAGState(
                query=query,
                user_location=context.get('location') if context else None,
                farmer_type=context.get('farmer_type') if context else None,
                retrieved_documents=[],
                knowledge_base_results=[],
                final_response={},
                confidence_score=0.0,
                processing_steps=[]
            )
            
            # Run the workflow
            result = self.app.invoke(initial_state)
            
            self.logger.info(f"Query processed successfully with confidence: {result['confidence_score']}")
            return result['final_response']
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return {
                "success": False,
                "error": f"Failed to process query: {str(e)}",
                "query": query
            }
    
    def _analyze_query(self, state: RAGState) -> RAGState:
        """Analyze the user query to extract intent and parameters"""
        query = state["query"].lower()
        steps = state["processing_steps"]
        steps.append("Query analysis started")
        
        # Extract farmer type from query
        farmer_type = state.get("farmer_type")
        if not farmer_type:
            if any(term in query for term in ["small farmer", "marginal farmer"]):
                farmer_type = "small/marginal"
            elif "large farmer" in query:
                farmer_type = "large"
            else:
                farmer_type = "all"
        
        # Extract state information
        user_location = state.get("user_location")
        target_state = None
        
        if user_location and user_location.get("state"):
            target_state = user_location["state"]
        else:
            # Try to extract state from query
            indian_states = [
                "andhra pradesh", "assam", "bihar", "gujarat", "haryana", 
                "karnataka", "kerala", "madhya pradesh", "maharashtra", 
                "odisha", "punjab", "rajasthan", "tamil nadu", "telangana",
                "uttar pradesh", "west bengal"
            ]
            
            for state in indian_states:
                if state in query:
                    target_state = state
                    break
        
        steps.append(f"Extracted farmer type: {farmer_type}, target state: {target_state}")
        
        return {
            **state,
            "farmer_type": farmer_type,
            "user_location": {**(state.get("user_location") or {}), "state": target_state},
            "processing_steps": steps
        }
    
    def _retrieve_from_vector_db(self, state: RAGState) -> RAGState:
        """Retrieve relevant documents from vector database"""
        query = state["query"]
        farmer_type = state.get("farmer_type")
        user_location = state.get("user_location", {})
        steps = state["processing_steps"]
        
        steps.append("Vector database retrieval started")
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings_manager.get_query_embedding(query)
            
            # Build filters
            filters = {}
            if user_location.get("state"):
                filters["state"] = user_location["state"]
            
            # Search vector database
            search_results = self.vector_db.search_similar(
                query_embedding=query_embedding,
                top_k=15,
                filters=filters if filters else None
            )
            
            # Process and rank results
            retrieved_docs = []
            for result in search_results:
                doc = {
                    "content": result["content"],
                    "metadata": result["metadata"],
                    "similarity": result["similarity"],
                    "source": result["collection"]
                }
                retrieved_docs.append(doc)
            
            steps.append(f"Retrieved {len(retrieved_docs)} documents from vector database")
            
        except Exception as e:
            self.logger.error(f"Error in vector retrieval: {e}")
            retrieved_docs = []
            steps.append(f"Vector retrieval failed: {str(e)}")
        
        return {
            **state,
            "retrieved_documents": retrieved_docs,
            "processing_steps": steps
        }
    
    def _search_knowledge_base(self, state: RAGState) -> RAGState:
        """Search structured knowledge base for relevant schemes"""
        query = state["query"]
        farmer_type = state.get("farmer_type")
        user_location = state.get("user_location", {})
        steps = state["processing_steps"]
        
        steps.append("Knowledge base search started")
        
        try:
            kb_results = []
            
            # Search by query text
            text_results = self.knowledge_base.search_schemes(query)
            for scheme_id, scheme, score in text_results[:10]:
                kb_results.append({
                    "scheme_id": scheme_id,
                    "scheme": scheme,
                    "relevance_score": score,
                    "source": "knowledge_base_text_search"
                })
            
            # Get state-specific schemes if location is available
            if user_location.get("state"):
                state_schemes = self.knowledge_base.get_schemes_by_state(user_location["state"])
                for scheme_id, scheme in state_schemes[:5]:
                    if not any(r["scheme_id"] == scheme_id for r in kb_results):
                        kb_results.append({
                            "scheme_id": scheme_id,
                            "scheme": scheme,
                            "relevance_score": 0.8,  # High relevance for state-specific
                            "source": "knowledge_base_state_specific"
                        })
            
            # Get irrigation schemes if query is about irrigation
            if any(term in query.lower() for term in ["irrigation", "drip", "micro irrigation", "water"]):
                irrigation_schemes = self.knowledge_base.get_irrigation_schemes()
                for scheme_id, scheme in irrigation_schemes[:5]:
                    if not any(r["scheme_id"] == scheme_id for r in kb_results):
                        kb_results.append({
                            "scheme_id": scheme_id,
                            "scheme": scheme,
                            "relevance_score": 0.9,  # High relevance for irrigation queries
                            "source": "knowledge_base_irrigation_specific"
                        })
            
            # Get farmer type specific schemes
            if farmer_type and farmer_type != "all":
                farmer_schemes = self.knowledge_base.get_schemes_for_farmer_type(farmer_type)
                for scheme_id, scheme in farmer_schemes[:5]:
                    if not any(r["scheme_id"] == scheme_id for r in kb_results):
                        kb_results.append({
                            "scheme_id": scheme_id,
                            "scheme": scheme,
                            "relevance_score": 0.7,
                            "source": "knowledge_base_farmer_type"
                        })
            
            # Sort by relevance score
            kb_results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            steps.append(f"Found {len(kb_results)} relevant schemes in knowledge base")
            
        except Exception as e:
            self.logger.error(f"Error in knowledge base search: {e}")
            kb_results = []
            steps.append(f"Knowledge base search failed: {str(e)}")
        
        return {
            **state,
            "knowledge_base_results": kb_results,
            "processing_steps": steps
        }
    
    def _synthesize_results(self, state: RAGState) -> RAGState:
        """Synthesize results from vector DB and knowledge base"""
        retrieved_docs = state["retrieved_documents"]
        kb_results = state["knowledge_base_results"]
        steps = state["processing_steps"]
        
        steps.append("Result synthesis started")
        
        # Combine and deduplicate results
        all_schemes = {}
        
        # Process knowledge base results (higher priority)
        for kb_result in kb_results:
            scheme = kb_result["scheme"]
            scheme_key = scheme.name.lower()
            
            if scheme_key not in all_schemes:
                all_schemes[scheme_key] = {
                    "name": scheme.name,
                    "description": scheme.description,
                    "eligibility": scheme.eligibility,
                    "benefits": scheme.benefits,
                    "subsidy_amount": scheme.subsidy_amount,
                    "application_process": scheme.application_process,
                    "required_documents": scheme.required_documents,
                    "application_links": scheme.application_links,
                    "implementing_agency": scheme.implementing_agency,
                    "state": scheme.state,
                    "category": scheme.category,
                    "status": scheme.status,
                    "contact_info": scheme.contact_info,
                    "source_urls": scheme.source_urls,
                    "relevance_score": kb_result["relevance_score"],
                    "data_source": "knowledge_base"
                }
        
        # Process vector database results
        for doc in retrieved_docs:
            metadata = doc["metadata"]
            scheme_name = metadata.get("scheme_name", "").lower()
            
            if scheme_name and scheme_name not in all_schemes:
                # Extract information from document content
                content = doc["content"]
                
                all_schemes[scheme_name] = {
                    "name": metadata.get("scheme_name", "Government Scheme"),
                    "description": content[:300] + "...",
                    "eligibility": self._extract_eligibility_from_content(content),
                    "benefits": self._extract_benefits_from_content(content),
                    "subsidy_amount": self._extract_subsidy_from_content(content),
                    "application_process": self._extract_application_process(content),
                    "required_documents": self._extract_documents_from_content(content),
                    "application_links": [metadata.get("url", "")],
                    "implementing_agency": metadata.get("source_domain", ""),
                    "state": metadata.get("state"),
                    "category": metadata.get("category", "general"),
                    "status": "active",
                    "contact_info": {},
                    "source_urls": [metadata.get("url", "")],
                    "relevance_score": doc["similarity"],
                    "data_source": "vector_database"
                }
        
        # Calculate overall confidence score
        if all_schemes:
            max_score = max(scheme["relevance_score"] for scheme in all_schemes.values())
            num_sources = len(set(scheme["data_source"] for scheme in all_schemes.values()))
            confidence = min(max_score * (1 + 0.2 * num_sources), 1.0)
        else:
            confidence = 0.0
        
        steps.append(f"Synthesized {len(all_schemes)} unique schemes with confidence {confidence:.2f}")
        
        return {
            **state,
            "synthesized_schemes": list(all_schemes.values()),
            "confidence_score": confidence,
            "processing_steps": steps
        }
    
    def _generate_response(self, state: RAGState) -> RAGState:
        """Generate final response for the user"""
        query = state["query"]
        schemes = state.get("synthesized_schemes", [])
        confidence = state["confidence_score"]
        steps = state["processing_steps"]
        
        steps.append("Response generation started")
        
        if not schemes:
            final_response = {
                "success": False,
                "message": "I couldn't find specific government schemes matching your query. Please try rephrasing your question or contact your local agricultural extension office.",
                "schemes": [],
                "confidence": 0.0,
                "suggestions": [
                    "Try using specific terms like 'drip irrigation subsidy' or 'seed subsidy'",
                    "Mention your state for state-specific schemes",
                    "Contact your local Krishi Vigyan Kendra for personalized assistance"
                ]
            }
        else:
            # Sort schemes by relevance
            schemes.sort(key=lambda x: x["relevance_score"], reverse=True)
            top_schemes = schemes[:5]  # Return top 5 most relevant schemes
            
            final_response = {
                "success": True,
                "message": f"Found {len(top_schemes)} relevant government schemes for your query.",
                "schemes": top_schemes,
                "confidence": confidence,
                "total_found": len(schemes),
                "query_processed": query,
                "farmer_recommendations": self._generate_farmer_recommendations(top_schemes, state.get("farmer_type"))
            }
        
        steps.append("Response generation completed")
        
        return {
            **state,
            "final_response": final_response,
            "processing_steps": steps
        }
    
    def _extract_eligibility_from_content(self, content: str) -> List[str]:
        """Extract eligibility criteria from content"""
        import re
        
        eligibility_patterns = [
            r'eligibility[:\s]*([^.\n]+)',
            r'eligible[:\s]*([^.\n]+)',
            r'(?:small|marginal|large)\s+farmer[s]?',
            r'land\s+holding[:\s]*([^.\n]+)'
        ]
        
        eligibility = []
        for pattern in eligibility_patterns:
            matches = re.findall(pattern, content, re.I)
            eligibility.extend([match.strip() for match in matches if match.strip()])
        
        return list(set(eligibility))[:3]  # Return unique, limited list
    
    def _extract_benefits_from_content(self, content: str) -> List[str]:
        """Extract benefits from content"""
        import re
        
        benefit_patterns = [
            r'benefit[s]?[:\s]*([^.\n]+)',
            r'subsidy[:\s]*([^.\n]+)',
            r'financial\s+assistance[:\s]*([^.\n]+)',
            r'₹[0-9,]+[^.\n]*'
        ]
        
        benefits = []
        for pattern in benefit_patterns:
            matches = re.findall(pattern, content, re.I)
            benefits.extend([match.strip() for match in matches if match.strip()])
        
        return list(set(benefits))[:3]
    
    def _extract_subsidy_from_content(self, content: str) -> Optional[str]:
        """Extract subsidy amount from content"""
        import re
        
        subsidy_patterns = [
            r'subsidy[:\s]*([^.\n]*(?:₹|rs|rupee)[^.\n]*)',
            r'(?:₹|rs\.?)\s*([0-9,]+(?:\.[0-9]+)?)[^.\n]*',
            r'([0-9]+%[^.\n]*subsidy)',
            r'up\s+to[:\s]*(₹[^.\n]+)'
        ]
        
        for pattern in subsidy_patterns:
            match = re.search(pattern, content, re.I)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_application_process(self, content: str) -> List[str]:
        """Extract application process from content"""
        import re
        
        process_patterns = [
            r'application[:\s]*([^.\n]+)',
            r'apply[:\s]*([^.\n]+)',
            r'procedure[:\s]*([^.\n]+)',
            r'step[s]?[:\s]*([^.\n]+)'
        ]
        
        process_steps = []
        for pattern in process_patterns:
            matches = re.findall(pattern, content, re.I)
            process_steps.extend([match.strip() for match in matches if match.strip()])
        
        return list(set(process_steps))[:3]
    
    def _extract_documents_from_content(self, content: str) -> List[str]:
        """Extract required documents from content"""
        import re
        
        doc_patterns = [
            r'documents?[:\s]*([^.\n]+)',
            r'(?:aadhaar|land\s+record|bank\s+details|income\s+certificate)'
        ]
        
        documents = []
        for pattern in doc_patterns:
            matches = re.findall(pattern, content, re.I)
            documents.extend([match.strip() for match in matches if match.strip()])
        
        return list(set(documents))[:3]
    
    def _generate_farmer_recommendations(self, schemes: List[Dict], farmer_type: Optional[str]) -> List[str]:
        """Generate personalized recommendations for farmers"""
        recommendations = []
        
        if farmer_type == "small/marginal":
            recommendations.append("Focus on schemes with lower eligibility thresholds and higher subsidy percentages")
            recommendations.append("Consider forming/joining Farmer Producer Organizations (FPOs) for better access")
        
        if any("irrigation" in scheme["name"].lower() or "water" in scheme["name"].lower() for scheme in schemes):
            recommendations.append("Drip irrigation can save 30-50% water and increase crop yield")
            recommendations.append("Apply during the right season for faster approval")
        
        recommendations.append("Keep all land documents and Aadhaar ready before applying")
        recommendations.append("Contact your local agricultural extension officer for guidance")
        
        return recommendations
