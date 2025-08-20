"""Plant Disease Diagnosis Agent for Agricultural Decision Support

This module provides multimodal plant disease diagnosis using advanced vision capabilities.
Designed specifically for Indian farmers with focus on local and affordable remedies.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
import base64
import time
import logging
from io import BytesIO
from PIL import Image
import requests

from ...infra.settings import settings
from ...infra.openai_service import openai_service
from ..prompts.plant_diagnosis import (
    PLANT_DIAGNOSIS_SYSTEM_PROMPT,
    PLANT_DIAGNOSIS_USER_TEMPLATE,
    TREATMENT_DETAILS_PROMPT
)


class PlantDocAgent:
    """Agricultural Plant Disease Diagnosis Agent with multimodal capabilities"""
    
    def __init__(self):
        # Agent only needs to interface with the OpenAI service, no direct API handling
        pass
        
    def encode_image_to_base64(self, image_file) -> str:
        """Convert image file to base64 string"""
        try:
            if hasattr(image_file, 'read'):
                # File-like object
                image_data = image_file.read()
                image_file.seek(0)  # Reset file pointer
            else:
                # Assume it's already bytes
                image_data = image_file
                
            # Convert to PIL Image to ensure format consistency
            image = Image.open(BytesIO(image_data))
            
            # Resize if too large (max 2048x2048 for efficiency)
            max_size = 2048
            if image.width > max_size or image.height > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save as JPEG with good quality
            buffer = BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            logging.error(f"Error encoding image: {e}")
            raise ValueError("Failed to process image file")

    def get_location_context(self, latitude: float, longitude: float) -> str:
        """Get contextual information about the farming region"""
        # Simplified Indian region detection based on coordinates
        regions = {
            'north': {'lat': (26, 37), 'lon': (68, 97), 'states': ['Punjab', 'Haryana', 'UP', 'Delhi', 'Rajasthan']},
            'south': {'lat': (8, 20), 'lon': (68, 87), 'states': ['Tamil Nadu', 'Karnataka', 'Kerala', 'Andhra Pradesh', 'Telangana']},
            'west': {'lat': (15, 28), 'lon': (68, 78), 'states': ['Maharashtra', 'Gujarat', 'Goa']},
            'east': {'lat': (18, 28), 'lon': (85, 97), 'states': ['West Bengal', 'Odisha', 'Jharkhand', 'Bihar']},
            'northeast': {'lat': (22, 30), 'lon': (88, 98), 'states': ['Assam', 'Meghalaya', 'Manipur', 'Tripura']},
            'central': {'lat': (18, 26), 'lon': (74, 87), 'states': ['Madhya Pradesh', 'Chhattisgarh']}
        }
        
        region_info = "India"
        for region, bounds in regions.items():
            if (bounds['lat'][0] <= latitude <= bounds['lat'][1] and 
                bounds['lon'][0] <= longitude <= bounds['lon'][1]):
                region_info = f"{region.title()} India ({', '.join(bounds['states'][:2])} region)"
                break
        
        return region_info

    def diagnose_plant_disease(
        self, 
        image_file,
        description: str = "",
        plant_name: str = "",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        place_name: Optional[str] = None,
        state: Optional[str] = None,
        language: str = "English"
    ) -> Dict[str, Any]:
        """
        Diagnose plant disease using multimodal AI analysis
        
        Args:
            image_file: Image file (bytes or file-like object)
            description: Optional text description of symptoms
            latitude: Farmer's latitude for regional context
            longitude: Farmer's longitude for regional context
            
        Returns:
            Structured diagnosis with treatment recommendations
        """
        start_time = time.time()
        
        try:
            # Encode image
            image_base64 = self.encode_image_to_base64(image_file)
            
            # Get regional context if coordinates provided
            location_context = "Location: Not specified"
            if latitude is not None and longitude is not None:
                if place_name and state:
                    location_context = f"Location: {place_name}, {state} (Lat: {latitude:.4f}, Lon: {longitude:.4f})"
                else:
                    region = self.get_location_context(latitude, longitude)
                    location_context = f"Location: {region} (Lat: {latitude:.4f}, Lon: {longitude:.4f})"
            
            # Prepare the prompt using extracted prompts
            user_content = PLANT_DIAGNOSIS_USER_TEMPLATE.format(
                location_context=location_context,
                plant_name=plant_name or "Not specified",
                description=description or "No additional symptoms described",
                language=language
            )
            
            # Make API request using OpenAI service
            response = openai_service.vision_completion(
                text_content=user_content,
                image_base64=image_base64,
                system_prompt=PLANT_DIAGNOSIS_SYSTEM_PROMPT,
                model="gpt-4o",
                max_tokens=4000,
                temperature=0.1,
                timeout=60
            )
            
            content = openai_service.extract_content(response)
            
            # Parse JSON response
            try:
                diagnosis_data = openai_service.parse_json_response(content)
                
                # Ensure all required fields exist
                diagnosis_data.setdefault('disease', 'Unknown Disease')
                diagnosis_data.setdefault('confidence', 0.5)
                diagnosis_data.setdefault('severity', 'medium')
                diagnosis_data.setdefault('symptoms', [])
                diagnosis_data.setdefault('treatment', [])
                diagnosis_data.setdefault('localRemedies', [])
                diagnosis_data.setdefault('prevention', [])
                diagnosis_data.setdefault('stage', 'Unknown')
                diagnosis_data.setdefault('affectedParts', [])
                diagnosis_data.setdefault('recommendedAction', 'Monitor plant health')
                diagnosis_data.setdefault('diseaseExplanation', 'Disease analysis in progress')
                diagnosis_data.setdefault('economicImpact', 'Economic impact assessment needed')
                diagnosis_data.setdefault('treatmentTiming', 'Apply treatments as soon as possible')
                diagnosis_data.setdefault('followUpCare', 'Monitor plant recovery and health')
                
            except json.JSONDecodeError as e:
                logging.error(f"JSON parsing failed: {e}, content: {content}")
                # Fallback response
                diagnosis_data = {
                    "disease": "Analysis Error",
                    "confidence": 0.0,
                    "severity": "unknown",
                    "symptoms": ["Unable to analyze image clearly"],
                    "treatment": ["Please consult local agricultural extension officer"],
                    "localRemedies": ["Ensure proper watering and sunlight"],
                    "prevention": ["Monitor plant health regularly"],
                    "stage": "Unknown",
                    "affectedParts": [],
                    "recommendedAction": "Retake image with better lighting"
                }
            
            # Add metadata
            diagnosis_data.update({
                "analysis_time": time.time() - start_time,
                "location": location_context,
                "model_used": "advanced-vision-model",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            logging.info(f"Plant diagnosis completed: {diagnosis_data['disease']} (confidence: {diagnosis_data['confidence']})")
            return diagnosis_data
            
        except Exception as e:
            logging.error(f"Plant diagnosis failed: {e}")
            return {
                "disease": "Analysis Failed",
                "confidence": 0.0,
                "severity": "unknown",
                "symptoms": ["Technical error occurred during analysis"],
                "treatment": ["Please try again or consult local expert"],
                "localRemedies": ["Basic plant care: adequate water, sunlight, and nutrition"],
                "prevention": ["Regular monitoring and proper plant care"],
                "stage": "Unknown",
                "affectedParts": [],
                "recommendedAction": "Retry analysis or seek expert help",
                "error": str(e),
                "analysis_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

    def get_treatment_details(self, disease_name: str, region: str = "India") -> Dict[str, Any]:
        """Get detailed treatment information for a specific disease"""
        try:
            prompt = TREATMENT_DETAILS_PROMPT.format(
                disease_name=disease_name,
                region=region
            )
            
            response = openai_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o",
                max_tokens=800,
                temperature=0.1,
                timeout=30
            )
            
            content = openai_service.extract_content(response)
            return openai_service.parse_json_response(content)
            
        except Exception as e:
            logging.error(f"Failed to get treatment details: {e}")
            return {
                "products": ["Consult local agricultural extension office"],
                "organicRemedies": ["Neem oil spray", "Compost application"],
                "application": ["Follow product instructions"],
                "timeline": ["Results expected in 7-14 days"],
                "cost": ["Varies by treatment option"]
            }
