from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from ..agent.agents.plant_doc_agent import PlantDocAgent

router = APIRouter()
plant_doc_agent = PlantDocAgent()

logger = logging.getLogger(__name__)


@router.post("/diagnose-plant")
async def diagnose_plant(
    image: UploadFile = File(...),
    description: Optional[str] = Form(""),
    plantName: Optional[str] = Form(""),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    placeName: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    language: Optional[str] = Form("English")
):
    """
    Diagnose plant disease from uploaded image with optional context
    """
    try:
        logger.info(f"Plant diagnosis request received - Image: {image.filename}, Description: {description[:50]}...")
        
        # Validate image file
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await image.read()
        
        if len(image_data) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="Image file too large (max 10MB)")
        
        # Perform diagnosis
        diagnosis_result = plant_doc_agent.diagnose_plant_disease(
            image_file=image_data,
            description=description or "",
            plant_name=plantName or "",
            latitude=latitude,
            longitude=longitude,
            place_name=placeName,
            state=state,
            language=language or "English"
        )
        
        logger.info(f"Plant diagnosis completed: {diagnosis_result.get('disease', 'Unknown')} (confidence: {diagnosis_result.get('confidence', 0)})")
        
        return JSONResponse(content=diagnosis_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Plant diagnosis error: {e}")
        # Provide specific error message based on the error type
        error_message = str(e)
        if "rate limit" in error_message.lower():
            disease_name = "Rate Limit Exceeded"
            symptoms = ["OpenAI API rate limit reached - too many requests"]
            treatment = ["Wait 1-2 minutes before trying again", "Consider upgrading OpenAI plan for higher limits"]
            action = "Please wait and try again in a few minutes"
        elif "api key" in error_message.lower():
            disease_name = "API Configuration Error"
            symptoms = ["OpenAI API key is invalid or missing"]
            treatment = ["Contact system administrator", "Verify API key configuration"]
            action = "System configuration issue - contact support"
        else:
            disease_name = "Plant Diagnosis Failed"
            symptoms = ["Technical error occurred during analysis"]
            treatment = ["Please try again or consult local expert"]
            action = "Retry analysis or seek expert help"
        
        return JSONResponse(
            status_code=500,
            content={
                "disease": disease_name,
                "confidence": 0.0,
                "severity": "unknown",
                "symptoms": symptoms,
                "treatment": treatment,
                "localRemedies": ["Basic plant care: adequate water, sunlight, and nutrition"],
                "prevention": ["Regular monitoring and proper plant care"],
                "stage": "Unknown",
                "affectedParts": [],
                "recommendedAction": action,
                "error": error_message,
                "timestamp": ""
            }
        )


@router.get("/treatment-details/{disease_name}")
async def get_treatment_details(disease_name: str, region: str = "India"):
    """
    Get detailed treatment information for a specific disease
    """
    try:
        logger.info(f"Treatment details requested for: {disease_name} in {region}")
        
        treatment_info = plant_doc_agent.get_treatment_details(disease_name, region)
        
        return JSONResponse(content=treatment_info)
        
    except Exception as e:
        logger.error(f"Treatment details error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to fetch treatment details",
                "products": ["Consult local agricultural extension office"],
                "organicRemedies": ["Neem oil spray", "Compost application"],
                "application": ["Follow product instructions"],
                "timeline": ["Results expected in 7-14 days"],
                "cost": ["Varies by treatment option"]
            }
        )
