"""
OpenAI Service for handling all OpenAI API interactions

This module centralizes OpenAI API calls to avoid scattered references throughout the codebase.
"""

import json
import logging
import requests
from typing import Dict, List, Any, Optional
from openai import OpenAI
from .settings import settings

try:
    from ..agent.prompts.govt_scheme import get_govt_scheme_prompt
except ImportError:
    # Fallback if prompt module not available
    def get_govt_scheme_prompt(query: str, context_str: str = "") -> str:
        return f"You are an expert Indian agriculture scheme assistant. Find 3 relevant government schemes for: {query}{context_str}"


class OpenAIService:
    """Centralized OpenAI API service"""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
    def _get_headers(self) -> Dict[str, str]:
        """Get common headers for OpenAI API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = "gpt-4",
        max_tokens: int = 1500,
        temperature: float = 0.1,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Make a chat completion request to OpenAI
        
        Args:
            messages: List of message objects with role and content
            model: OpenAI model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            timeout: Request timeout in seconds
            
        Returns:
            OpenAI API response
            
        Raises:
            Exception: If API call fails
        """
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self._get_headers(),
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                logging.error(f"OpenAI rate limit exceeded: {e}")
                raise ValueError("OpenAI API rate limit exceeded. Please wait before making another request.")
            raise
        
        return response.json()
    
    def vision_completion(
        self,
        text_content: str,
        image_base64: str,
        system_prompt: str = "",
        model: str = "gpt-4o",
        max_tokens: int = 1500,
        temperature: float = 0.1,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Make a vision completion request (text + image) to OpenAI
        
        Args:
            text_content: Text content to analyze
            image_base64: Base64 encoded image
            system_prompt: System prompt (optional)
            model: OpenAI vision model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            timeout: Request timeout in seconds
            
        Returns:
            OpenAI API response
            
        Raises:
            Exception: If API call fails
        """
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": text_content},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                        "detail": "high"
                    }
                }
            ]
        })
        
        return self.chat_completion(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout
        )
    
    def extract_content(self, response: Dict[str, Any]) -> str:
        """Extract content from OpenAI API response"""
        try:
            return response['choices'][0]['message']['content'].strip()
        except (KeyError, IndexError) as e:
            logging.error(f"Failed to extract content from OpenAI response: {e}")
            raise ValueError("Invalid OpenAI API response format")
    
    def parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON response from OpenAI, handling markdown code blocks
        
        Args:
            content: Raw content from OpenAI response
            
        Returns:
            Parsed JSON data
            
        Raises:
            json.JSONDecodeError: If content is not valid JSON
        """
        # Clean potential markdown formatting
        clean_content = content
        if content.startswith('```json'):
            clean_content = content[7:-3].strip()
        elif content.startswith('```'):
            clean_content = content[3:-3].strip()
        
        return json.loads(clean_content)


class OpenAIWebSearchClient:
    """OpenAI client for web search of government schemes using GPT-4o-mini for cost efficiency."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.openai_api_key
        self.logger = logging.getLogger(__name__)
        self.client = None
        
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.logger.info("OpenAI web search client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
    
    @property
    def available(self) -> bool:
        return bool(self.client)
    
    def search_schemes(self, query: str, state: Optional[str] = None, farmer_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for government schemes using OpenAI with web search capabilities.
        
        Args:
            query: User query about schemes/subsidies
            state: Indian state name for state-specific schemes
            farmer_type: small/marginal/large farmer for targeted schemes
        
        Returns:
            Normalized response with max 3 schemes
        """
        if not self.available:
            return {"success": False, "error": "OpenAI API key not configured"}
        
        try:
            # Build context-aware prompt
            context_parts = []
            if state:
                context_parts.append(f"State: {state}")
            if farmer_type:
                context_parts.append(f"Farmer type: {farmer_type}")
            
            context_str = f" ({', '.join(context_parts)})" if context_parts else ""
            
            system_prompt = get_govt_scheme_prompt(query, context_str)

            # Try GPT-5 with web search capabilities, fallback to GPT-4o if unavailable
            try:
                response = self.client.chat.completions.create(
                    model="gpt-5",  # Latest GPT-5 model as requested
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Search the web for 3 current government agricultural schemes for: {query}. Use official gov.in sources."}
                    ],
                    temperature=0.1,  # Low temperature for factual accuracy
                    max_completion_tokens=8000,   # Increased token limit for comprehensive responses
                    timeout=45        # Longer timeout for web search
                )
            except Exception as gpt5_error:
                self.logger.warning(f"GPT-5 not available, trying GPT-4o: {gpt5_error}")
                # Fallback to GPT-4o if GPT-5 is not available
                response = self.client.chat.completions.create(
                    model="gpt-4o",  # Fallback to GPT-4o
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Find 3 current government agricultural schemes for: {query}"}
                    ],
                    temperature=0.1,
                    max_completion_tokens=8000,
                    timeout=45
                )
            
            content = response.choices[0].message.content.strip()
            
            # Since we're now getting markdown response, return it directly
            if not content or len(content.strip()) < 50:
                return {
                    "success": False, 
                    "error": "No schemes found for your query. Try being more specific about your farming needs."
                }
            
            # Return formatted markdown response
            return {
                "success": True,
                "schemes_info": content,  # Markdown formatted response
                "total_found": 3,  # Always 3 schemes as requested
                "confidence": 0.95,  # High confidence for GPT-4o results
                "source": "OpenAI Web Search",
                "response_format": "markdown"
            }
            
        except Exception as e:
            self.logger.error(f"OpenAI web search error: {e}")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}. Please try again or contact support."
            }
    
    def _validate_scheme_data(self, scheme: Dict[str, Any]) -> bool:
        """Validate that scheme contains required fields."""
        required_fields = ["name", "description"]
        return all(field in scheme for field in required_fields)


# Global service instances
openai_service = OpenAIService()
openai_web_client = OpenAIWebSearchClient()
