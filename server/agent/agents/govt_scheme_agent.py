"""Government Scheme Agent for Indian Agricultural Schemes

Core approach: OpenAI web search with RAG fallback.
We use OpenAI's web search capabilities to find current government schemes.
RAG system is available as a backup when needed.
"""

import logging
from typing import Dict, Any, Optional
from ..rag.lightweight_rag_agent import LightweightRAGAgent
from pathlib import Path
from ...infra.settings import settings
from ...infra.openai_service import openai_web_client

class GovtSchemeAgent:
    """Government Scheme Agent using OpenAI web search for government scheme information.

    Primary approach: OpenAI web search for current, accurate scheme details.
    RAG system available as fallback when needed.
    """
    
    def __init__(self, 
                 db_path: str = "./govt_schemes_lightweight.db"):
        self.logger = logging.getLogger(__name__)
        
        # Initialize lightweight RAG system
        self.rag_agent = LightweightRAGAgent(db_path=db_path)
        # OpenAI web search is the primary method
        self.openai_client = openai_web_client
        
        self.logger.info("Government Scheme Agent initialized with lightweight RAG system")
    
    def search_schemes(self, query: str, state: Optional[str] = None, farmer_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for government agricultural schemes using RAG system
        
        Args:
            query: User query about schemes/subsidies
            state: Indian state name for state-specific schemes
            farmer_type: small/marginal/large farmer for targeted schemes
        """
        try:
            self.logger.info(f"Processing government scheme query: {query}")
            
            # Prepare context for RAG agent
            context = {}
            
            if state:
                context['location'] = {'state': state}
            
            if farmer_type:
                context['farmer_type'] = farmer_type
            
            # Use OpenAI web search for government schemes
            if self.openai_client.available:
                oa_result = self.openai_client.search_schemes(query, state, farmer_type)
                if oa_result.get("success"):
                    return {
                        "success": True,
                        "data": {
                            "schemes_info": oa_result.get("schemes_info", ""),
                            "total_schemes_found": oa_result.get('total_found', 3),
                            "confidence": oa_result.get('confidence', 0.95),
                            "query": query,
                            "search_context": {"state": state, "farmer_type": farmer_type}
                        },
                        "source": "OpenAI Web Search",
                        "agricultural_use": "Government scheme discovery, eligibility, application guidance"
                    }

            # Fallback error message if OpenAI is not available
            return {
                "success": False,
                "error": (
                    "Unable to fetch government scheme details right now. "
                    "Please try again in a moment or refine your query with more details."
                ),
                "query": query
            }
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return {
                "success": False,
                "error": f"Processing error: {str(e)}",
                "query": query
            }
    
    def _format_schemes_response(self, schemes: list, rag_response: dict) -> str:
        """Format schemes into a comprehensive response text"""
        if not schemes:
            return "No relevant government schemes found."
        
        response_parts = []
        
        # Add summary
        total_found = rag_response.get('total_found', len(schemes))
        confidence = rag_response.get('confidence', 0.0)
        
        response_parts.append(f"Found {len(schemes)} relevant government schemes (Total: {total_found}, Confidence: {confidence:.1%}):\n")
        
        # Add each scheme details
        for i, scheme in enumerate(schemes[:3], 1):  # Limit to top 3 schemes
            scheme_text = f"{i}. **{scheme.get('name', 'Government Scheme')}**\n"
            
            # Description
            if scheme.get('description'):
                description = scheme['description'][:200] + "..." if len(scheme['description']) > 200 else scheme['description']
                scheme_text += f"   Description: {description}\n"
            
            # Eligibility
            if scheme.get('eligibility'):
                eligibility = ", ".join(scheme['eligibility'][:3])
                scheme_text += f"   Eligibility: {eligibility}\n"
            
            # Subsidy Amount
            if scheme.get('subsidy_amount'):
                scheme_text += f"   Subsidy: {scheme['subsidy_amount']}\n"
            
            # Required Documents
            if scheme.get('required_documents'):
                docs = ", ".join(scheme['required_documents'][:3])
                scheme_text += f"   Required Documents: {docs}\n"
            
            # Application Links
            if scheme.get('application_links'):
                links = [link for link in scheme['application_links'] if link]
                if links:
                    scheme_text += f"   Apply Online: {links[0]}\n"
            
            # State Information
            if scheme.get('state'):
                scheme_text += f"   State: {scheme['state'].title()}\n"
            
            # Agency
            if scheme.get('implementing_agency'):
                scheme_text += f"   Implementing Agency: {scheme['implementing_agency']}\n"
            
            scheme_text += "\n"
            response_parts.append(scheme_text)
        
        # Add farmer recommendations
        recommendations = rag_response.get('farmer_recommendations', [])
        if recommendations:
            response_parts.append("**Recommendations for Farmers:**")
            for rec in recommendations:
                response_parts.append(f"• {rec}")
            response_parts.append("")
        
        # Add general advice
        response_parts.extend([
            "**Next Steps:**",
            "• Verify eligibility criteria carefully before applying",
            "• Keep all required documents ready",
            "• Contact your local agricultural extension officer for guidance",
            "• Apply within the specified deadlines",
            "",
            "**Need More Help?**",
            "• Visit your nearest Krishi Vigyan Kendra (KVK)",
            "• Call the Kisan Call Centre: 1551",
            "• Visit the official PM-KISAN website: pmkisan.gov.in"
        ])
        
        return "\n".join(response_parts)

    def _to_structured_schemes(self, schemes: list) -> list:
        """Map various scheme shapes into strict schema required by frontend.

        Output item schema:
        {
          "scheme_name": str,
          "description": str,
          "eligibility": str,
          "benefits": str,
          "application_process": str,
          "application_link": str | None,
          "source_url": str | None,
          "state": str | None
        }
        """
        out = []
        for s in (schemes or [])[:3]:
            name = s.get('name') or s.get('scheme_name') or 'Government Scheme'
            desc = s.get('description') or ''
            elig = s.get('eligibility') or []
            if isinstance(elig, list):
                elig_text = ", ".join([e for e in elig if isinstance(e, str)])
            else:
                elig_text = str(elig)
            subsidy = s.get('subsidy_amount') or s.get('benefits') or ''
            benefits = subsidy if isinstance(subsidy, str) else str(subsidy)
            docs = s.get('required_documents') or []
            if isinstance(docs, list) and docs:
                process = "Apply online and upload: " + ", ".join([d for d in docs if isinstance(d, str)][:5])
            else:
                process = "Apply online via official portal."
            links = s.get('application_links') or []
            link = None
            if isinstance(links, list) and links:
                link = links[0]
            elif isinstance(links, str):
                link = links
            item = {
                "scheme_name": name,
                "description": desc,
                "eligibility": elig_text,
                "benefits": benefits,
                "application_process": process,
                "application_link": link,
                "source_url": s.get('source_url'),
                "state": s.get('state')
            }
            out.append(item)
        return out

    def _collect_sources(self, schemes: list) -> list:
        urls = []
        for s in schemes or []:
            if s.get('source_url'):
                urls.append(s['source_url'])
            links = s.get('application_links') or []
            if isinstance(links, list):
                urls.extend([l for l in links if isinstance(l, str)])
            elif isinstance(links, str):
                urls.append(links)
        # de-duplicate while preserving order
        seen = set()
        uniq = []
        for u in urls:
            if u and u not in seen:
                seen.add(u)
                uniq.append(u)
        return uniq
    
    async def force_reindex(self) -> Dict[str, Any]:
        """Manually trigger reindexing of government sources"""
        try:
            self.logger.info("Starting manual reindexing...")
            stats = await self.rag_agent.index_government_sources()
            
            return {
                "success": True,
                "message": "Manual reindexing completed",
                "stats": stats
            }
            
        except Exception as e:
            self.logger.error(f"Error during manual reindexing: {e}")
            return {
                "success": False,
                "error": f"Reindexing failed: {str(e)}"
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of the RAG system"""
        status = {
            "rag_system": "operational",
            "database_stats": {},
            "system_type": "lightweight"
        }
        
        try:
            # Get database statistics
            status["database_stats"] = self.rag_agent.get_system_stats()
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            status["error"] = str(e)
        
        return status
    
    def shutdown(self):
        """Shutdown the agent"""
        self.rag_agent.close()
        self.logger.info("Government Scheme Agent shutdown complete")


# Global instance
govt_scheme_agent = GovtSchemeAgent()
