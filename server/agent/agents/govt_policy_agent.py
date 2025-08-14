"""
Government Policy Agent for Indian Agricultural Schemes

Uses Perplexity Sonar API for real-time search of government schemes,
subsidies, and policies relevant to Indian farmers.
"""

import requests
from typing import Dict, Any, Optional
from ...infra.settings import settings


class GovtPolicyAgent:
    """Government Policy Agent using Perplexity Sonar for accurate scheme information"""
    
    def __init__(self):
        self.perplexity_api_key = settings.perplexity_api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
    
    def search_schemes(self, query: str, state: Optional[str] = None, farmer_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for government agricultural schemes using Perplexity Sonar
        
        Args:
            query: User query about schemes/subsidies
            state: Indian state name for state-specific schemes
            farmer_type: small/marginal/large farmer for targeted schemes
        """
        if not self.perplexity_api_key:
            return {
                "success": False,
                "error": "Perplexity API key not configured. Set PERPLEXITY_API_KEY environment variable."
            }
        
        # Build search-optimized prompt
        search_prompt = self._build_search_prompt(query, state, farmer_type)
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.perplexity_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-sonar-large-128k-online",  # Perplexity Sonar model
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are an expert on Indian government agricultural schemes and policies. Provide accurate, up-to-date information with official sources and application links."
                        },
                        {"role": "user", "content": search_prompt}
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.1,  # Low temperature for accuracy
                    "return_citations": True
                },
                timeout=20
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract response and citations
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            citations = data.get("citations", [])
            
            return {
                "success": True,
                "data": {
                    "schemes_info": content,
                    "sources": citations,
                    "query": query,
                    "search_context": {"state": state, "farmer_type": farmer_type}
                },
                "source": "Perplexity Sonar API",
                "agricultural_use": "Government scheme discovery, eligibility checking, application guidance"
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"API request failed: {str(e)}",
                "query": query
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Processing error: {str(e)}",
                "query": query
            }
    
    def _build_search_prompt(self, query: str, state: Optional[str], farmer_type: Optional[str]) -> str:
        """Build optimized search prompt for government schemes"""
        
        # Base prompt focusing on Indian government sources
        prompt_parts = [
            f"Search for Indian government agricultural schemes related to: {query}",
            "Focus on official government websites (.gov.in domains)",
            "Include specific details about:"
        ]
        
        details = [
            "- Scheme name and current status",
            "- Eligibility criteria (land size, farmer category, income limits)", 
            "- Subsidy amounts and percentages",
            "- Required documents",
            "- Application process and deadlines",
            "- Official application links and contact information"
        ]
        
        prompt_parts.extend(details)
        
        # Add state-specific context
        if state:
            prompt_parts.append(f"Prioritize schemes available in {state} state of India.")
        
        # Add farmer type context  
        if farmer_type:
            prompt_parts.append(f"Focus on schemes for {farmer_type} farmers.")
        
        # Add source preference
        prompt_parts.extend([
            "",
            "Preferred sources: pmkisan.gov.in, agricoop.nic.in, mkisan.gov.in, dahd.nic.in, state government agriculture portals",
            "Provide direct links to application forms and official notifications."
        ])
        
        return "\n".join(prompt_parts)


# Global instance
govt_policy_agent = GovtPolicyAgent()
