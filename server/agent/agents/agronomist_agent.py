"""
Agronomist Agent for Agricultural Decision Support

This module provides comprehensive agronomic advice using GPT-4o for crop recommendations,
farming techniques, variety selection, and agricultural best practices for Indian farmers.
"""

from __future__ import annotations
from typing import Any, Dict, Optional
import time
import logging

from ...infra.openai_service import openai_service
from ..prompts.agronomist import (
    AGRONOMIST_SYSTEM_PROMPT,
    AGRONOMIST_USER_TEMPLATE,
    CROP_RECOMMENDATION_PROMPT,
    VARIETY_SELECTION_PROMPT,
    FARMING_TECHNIQUE_PROMPT
)


class AgronomistAgent:
    """Agricultural Expert Agent for comprehensive farming advice using GPT-4o"""
    
    def __init__(self):
        # Agent interfaces with OpenAI service for GPT-4o calls
        self.logger = logging.getLogger(__name__)
        
    def get_agronomic_advice(
        self,
        query: str,
        location_context: Optional[str] = None,
        season: Optional[str] = None,
        farmer_type: Optional[str] = None,
        farm_size: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive agronomic advice for farming queries
        
        Args:
            query: The farming question or problem
            location_context: Location information (state, district, climate zone)
            season: Current season (Kharif, Rabi, Zaid, or specific months)
            farmer_type: Type of farmer (small, marginal, large, etc.)
            farm_size: Size of farm (acres/hectares)
            additional_context: Any additional relevant information
            
        Returns:
            Structured agronomic advice with recommendations and reasoning
        """
        start_time = time.time()
        
        try:
            # Prepare the prompt using template
            user_content = AGRONOMIST_USER_TEMPLATE.format(
                query=query,
                location_context=location_context or "Not specified",
                season=season or "Not specified",
                farmer_type=farmer_type or "Not specified", 
                farm_size=farm_size or "Not specified",
                additional_context=additional_context or "No additional context"
            )
            
            # Make API request using OpenAI service
            response = openai_service.chat_completion(
                messages=[
                    {"role": "system", "content": AGRONOMIST_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                model="gpt-4o",
                max_tokens=1500,
                temperature=0.1,  # Low temperature for factual accuracy
                timeout=45
            )
            
            content = openai_service.extract_content(response)
            
            if not content or len(content.strip()) < 20:
                return {
                    "tool": "get_agronomic_advice",
                    "success": False,
                    "error": "No advice generated. Please provide more specific details about your farming question.",
                    "query": query
                }
            
            return {
                "tool": "get_agronomic_advice",
                "success": True,
                "data": {
                    "advice": content,
                    "query": query,
                    "context": {
                        "location": location_context,
                        "season": season,
                        "farmer_type": farmer_type,
                        "farm_size": farm_size
                    }
                },
                "source": "GPT-4o Agricultural Expert",
                "analysis_time": round(time.time() - start_time, 2),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "agricultural_use": "Comprehensive farming advice and crop management guidance"
            }
            
        except Exception as e:
            self.logger.error(f"Agronomic advice generation failed: {e}")
            return {
                "tool": "get_agronomic_advice",
                "success": False,
                "error": f"Failed to generate advice: {str(e)}. Please try again with more specific details.",
                "query": query,
                "analysis_time": round(time.time() - start_time, 2),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def recommend_crops(
        self,
        soil_type: str,
        region: str,
        season: str,
        water_availability: str = "moderate",
        farm_size: str = "small",
        budget: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Recommend suitable crops based on farming conditions
        
        Args:
            soil_type: Type of soil (clay, loam, sandy, etc.)
            region: Geographic region or climate zone
            season: Growing season (Kharif, Rabi, Zaid)
            water_availability: Water access (low, moderate, high)
            farm_size: Size category (small, medium, large)
            budget: Budget range (low, moderate, high)
            
        Returns:
            Crop recommendations with detailed analysis
        """
        start_time = time.time()
        
        try:
            prompt = CROP_RECOMMENDATION_PROMPT.format(
                soil_type=soil_type,
                region=region,
                season=season,
                water_availability=water_availability,
                farm_size=farm_size,
                budget=budget
            )
            
            response = openai_service.chat_completion(
                messages=[
                    {"role": "system", "content": AGRONOMIST_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-4o",
                max_tokens=1200,
                temperature=0.1,
                timeout=40
            )
            
            content = openai_service.extract_content(response)
            
            return {
                "tool": "recommend_crops",
                "success": True,
                "data": {
                    "recommendations": content,
                    "conditions": {
                        "soil_type": soil_type,
                        "region": region,
                        "season": season,
                        "water_availability": water_availability,
                        "farm_size": farm_size,
                        "budget": budget
                    }
                },
                "source": "GPT-4o Crop Recommendation System",
                "analysis_time": round(time.time() - start_time, 2),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "agricultural_use": "Crop selection and planning guidance"
            }
            
        except Exception as e:
            self.logger.error(f"Crop recommendation failed: {e}")
            return {
                "tool": "recommend_crops",
                "success": False,
                "error": f"Failed to generate crop recommendations: {str(e)}",
                "analysis_time": round(time.time() - start_time, 2),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def recommend_varieties(
        self,
        crop_name: str,
        climate_conditions: str,
        soil_conditions: str,
        water_conditions: str,
        season: str,
        duration_preference: str = "medium",
        yield_expectation: str = "high",
        market_type: str = "local",
        disease_resistance: str = "high"
    ) -> Dict[str, Any]:
        """
        Recommend specific crop varieties based on conditions and requirements
        
        Args:
            crop_name: Name of the crop
            climate_conditions: Climate description
            soil_conditions: Soil characteristics
            water_conditions: Water availability and quality
            season: Growing season
            duration_preference: Preferred crop duration (short, medium, long)
            yield_expectation: Expected yield level (low, medium, high)
            market_type: Target market (local, regional, export)
            disease_resistance: Disease resistance requirement (low, medium, high)
            
        Returns:
            Variety recommendations with detailed comparison
        """
        start_time = time.time()
        
        try:
            prompt = VARIETY_SELECTION_PROMPT.format(
                crop_name=crop_name,
                climate_conditions=climate_conditions,
                soil_conditions=soil_conditions,
                water_conditions=water_conditions,
                season=season,
                duration_preference=duration_preference,
                yield_expectation=yield_expectation,
                market_type=market_type,
                disease_resistance=disease_resistance
            )
            
            response = openai_service.chat_completion(
                messages=[
                    {"role": "system", "content": AGRONOMIST_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-4o",
                max_tokens=1200,
                temperature=0.1,
                timeout=40
            )
            
            content = openai_service.extract_content(response)
            
            return {
                "tool": "recommend_varieties",
                "success": True,
                "data": {
                    "variety_recommendations": content,
                    "crop": crop_name,
                    "requirements": {
                        "climate": climate_conditions,
                        "soil": soil_conditions,
                        "water": water_conditions,
                        "season": season,
                        "duration": duration_preference,
                        "yield": yield_expectation,
                        "market": market_type,
                        "resistance": disease_resistance
                    }
                },
                "source": "GPT-4o Variety Selection Expert",
                "analysis_time": round(time.time() - start_time, 2),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "agricultural_use": "Crop variety selection and optimization"
            }
            
        except Exception as e:
            self.logger.error(f"Variety recommendation failed: {e}")
            return {
                "tool": "recommend_varieties",
                "success": False,
                "error": f"Failed to generate variety recommendations: {str(e)}",
                "analysis_time": round(time.time() - start_time, 2),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def get_farming_technique_advice(
        self,
        technique_type: str,
        crop_name: str,
        region: str,
        current_practice: str = "traditional",
        challenges: str = "",
        resources: str = "limited",
        goals: str = "increase yield"
    ) -> Dict[str, Any]:
        """
        Get advice on specific farming techniques and practices
        
        Args:
            technique_type: Type of technique (irrigation, fertilization, pest control, etc.)
            crop_name: Crop for which advice is needed
            region: Geographic region
            current_practice: Current farming practice being used
            challenges: Specific challenges being faced
            resources: Available resources (limited, moderate, good)
            goals: Specific goals (increase yield, reduce cost, etc.)
            
        Returns:
            Detailed farming technique recommendations
        """
        start_time = time.time()
        
        try:
            prompt = FARMING_TECHNIQUE_PROMPT.format(
                technique_type=technique_type,
                crop_name=crop_name,
                region=region,
                current_practice=current_practice,
                challenges=challenges or "No specific challenges mentioned",
                resources=resources,
                goals=goals
            )
            
            response = openai_service.chat_completion(
                messages=[
                    {"role": "system", "content": AGRONOMIST_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-4o",
                max_tokens=1200,
                temperature=0.1,
                timeout=40
            )
            
            content = openai_service.extract_content(response)
            
            return {
                "tool": "get_farming_technique_advice",
                "success": True,
                "data": {
                    "technique_advice": content,
                    "technique_type": technique_type,
                    "crop": crop_name,
                    "context": {
                        "region": region,
                        "current_practice": current_practice,
                        "challenges": challenges,
                        "resources": resources,
                        "goals": goals
                    }
                },
                "source": "GPT-4o Farming Technique Expert",
                "analysis_time": round(time.time() - start_time, 2),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "agricultural_use": "Farming technique optimization and improvement"
            }
            
        except Exception as e:
            self.logger.error(f"Farming technique advice failed: {e}")
            return {
                "tool": "get_farming_technique_advice",
                "success": False,
                "error": f"Failed to generate technique advice: {str(e)}",
                "analysis_time": round(time.time() - start_time, 2),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }


# Global agronomist agent instance
agronomist_agent = AgronomistAgent()
