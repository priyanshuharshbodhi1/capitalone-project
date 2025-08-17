"""
OpenAI Service for handling all OpenAI API interactions

This module centralizes OpenAI API calls to avoid scattered references throughout the codebase.
"""

import json
import logging
import requests
from typing import Dict, List, Any, Optional
from .settings import settings


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


# Global service instance
openai_service = OpenAIService()
