"""Weather Agent for Agricultural Decision Support

This module provides 4 specialized weather tools for Indian farmers using Open-Meteo and OpenWeather APIs.
Each tool is designed for specific agricultural use cases and returns structured data for LLM interpretation.
"""

from __future__ import annotations
from typing import Any, Dict, Optional
import time
import requests
from ...infra.settings import settings


class WeatherAgent:
    """Agricultural Weather Agent with 4 specialized tools following OpenAI tool calling format"""
    
    def __init__(self):
        self.openweather_api_key = settings.openweather_api_key
    
    # TOOL 1: Get current weather conditions for immediate agricultural decisions
    # Use for: Should I irrigate now? Is it safe to spray pesticides? Current soil conditions?
    # Parameters: lat (float), lon (float)
    # Response: Current temperature, humidity, precipitation, soil temperature, soil moisture
    def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get real-time weather conditions including soil parameters for immediate farm decisions"""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,soil_temperature_0cm,soil_moisture_0_1cm",
            "timezone": "auto"
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            current = data.get("current", {})
            return {
                "tool": "get_current_weather",
                "success": True,
                "data": {
                    "temperature_celsius": current.get("temperature_2m"),
                    "humidity_percent": current.get("relative_humidity_2m"),
                    "precipitation_mm": current.get("precipitation"),
                    "soil_temperature_celsius": current.get("soil_temperature_0cm"),
                    "soil_moisture_percent": current.get("soil_moisture_0_1cm"),
                    "timestamp": current.get("time"),
                    "location": {"lat": lat, "lon": lon}
                },
                "source": "Open-Meteo Current API",
                "agricultural_use": "Real-time irrigation decisions, pesticide application timing, soil condition assessment"
            }
        except Exception as e:
            return {
                "tool": "get_current_weather",
                "success": False,
                "error": str(e),
                "location": {"lat": lat, "lon": lon}
            }
    
    # TOOL 2: Get future weather forecast for crop planning and protection
    # Use for: Should I plant next week? When will it rain? Planning harvest timing?
    # Parameters: lat (float), lon (float), days (int, default=7, max=16)
    # Response: Daily max/min temperatures, precipitation forecast for planning
    def get_future_weather(self, lat: float, lon: float, days: int = 7) -> Dict[str, Any]:
        """Get weather forecast for crop planning, planting, and harvest timing decisions"""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "forecast_days": min(days, 16),  # Open-Meteo max is 16 days
            "timezone": "auto"
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            max_temps = daily.get("temperature_2m_max", [])
            min_temps = daily.get("temperature_2m_min", [])
            precipitation = daily.get("precipitation_sum", [])
            
            forecast = []
            for i in range(len(dates)):
                forecast.append({
                    "date": dates[i],
                    "max_temp_celsius": max_temps[i] if i < len(max_temps) else None,
                    "min_temp_celsius": min_temps[i] if i < len(min_temps) else None,
                    "precipitation_mm": precipitation[i] if i < len(precipitation) else None
                })
            
            return {
                "tool": "get_future_weather",
                "success": True,
                "data": {
                    "forecast_days": len(forecast),
                    "daily_forecast": forecast,
                    "location": {"lat": lat, "lon": lon}
                },
                "source": "Open-Meteo Forecast API",
                "agricultural_use": "Crop planning, planting decisions, harvest timing, irrigation scheduling"
            }
        except Exception as e:
            return {
                "tool": "get_future_weather",
                "success": False,
                "error": str(e),
                "location": {"lat": lat, "lon": lon},
                "requested_days": days
            }
    
    # TOOL 3: Get historical weather patterns for crop selection and yield analysis
    # Use for: What crops suited last year's weather? Comparing current season to past years?
    # Parameters: lat (float), lon (float), start_date (str, YYYY-MM-DD), end_date (str, YYYY-MM-DD)
    # Response: Historical temperature and precipitation data for pattern analysis
    def get_historical_weather(self, lat: float, lon: float, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get historical weather data for crop selection and seasonal pattern analysis"""
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,precipitation_sum",
            "timezone": "auto"
        }
        
        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            max_temps = daily.get("temperature_2m_max", [])
            precipitation = daily.get("precipitation_sum", [])
            
            historical_data = []
            for i in range(len(dates)):
                historical_data.append({
                    "date": dates[i],
                    "max_temp_celsius": max_temps[i] if i < len(max_temps) else None,
                    "precipitation_mm": precipitation[i] if i < len(precipitation) else None
                })
            
            # Calculate summary statistics
            temps = [d["max_temp_celsius"] for d in historical_data if d["max_temp_celsius"] is not None]
            precip = [d["precipitation_mm"] for d in historical_data if d["precipitation_mm"] is not None]
            
            summary = {}
            if temps:
                summary["temperature"] = {
                    "avg_max_celsius": round(sum(temps) / len(temps), 1),
                    "highest_celsius": max(temps),
                    "lowest_celsius": min(temps)
                }
            if precip:
                summary["precipitation"] = {
                    "total_mm": sum(precip),
                    "avg_daily_mm": round(sum(precip) / len(precip), 1),
                    "max_daily_mm": max(precip)
                }
            
            return {
                "tool": "get_historical_weather",
                "success": True,
                "data": {
                    "period": {"start": start_date, "end": end_date},
                    "total_days": len(historical_data),
                    "daily_data": historical_data,
                    "summary": summary,
                    "location": {"lat": lat, "lon": lon}
                },
                "source": "Open-Meteo Historical Archive API",
                "agricultural_use": "Crop variety selection, seasonal planning, yield comparison, climate pattern analysis"
            }
        except Exception as e:
            return {
                "tool": "get_historical_weather",
                "success": False,
                "error": str(e),
                "location": {"lat": lat, "lon": lon},
                "requested_period": {"start": start_date, "end": end_date}
            }
    
    # TOOL 4: Get weather alerts for crop protection and emergency planning
    # Use for: Are there storms coming? Should I protect crops? Emergency weather warnings?
    # Parameters: lat (float), lon (float)
    # Response: Active weather alerts, warnings, and emergency notifications
    def get_weather_alerts(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get weather alerts and warnings for crop protection and emergency planning"""
        if not self.openweather_api_key:
            return {
                "tool": "get_weather_alerts",
                "success": False,
                "error": "OpenWeather API key required for alerts. Set OPENWEATHER_API_KEY environment variable.",
                "location": {"lat": lat, "lon": lon}
            }
        
        url = "https://api.openweathermap.org/data/3.0/onecall"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.openweather_api_key,
            "exclude": "minutely,hourly,daily"  # Only get current and alerts
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            alerts = data.get("alerts", [])
            processed_alerts = []
            
            for alert in alerts:
                processed_alerts.append({
                    "event": alert.get("event"),
                    "description": alert.get("description"),
                    "start_time": alert.get("start"),
                    "end_time": alert.get("end"),
                    "sender": alert.get("sender_name"),
                    "severity": "high" if any(word in alert.get("event", "").lower() for word in ["severe", "warning", "extreme"]) else "medium"
                })
            
            return {
                "tool": "get_weather_alerts",
                "success": True,
                "data": {
                    "alert_count": len(processed_alerts),
                    "alerts": processed_alerts,
                    "has_severe_alerts": any(alert["severity"] == "high" for alert in processed_alerts),
                    "location": {"lat": lat, "lon": lon}
                },
                "source": "OpenWeather OneCall API 3.0",
                "agricultural_use": "Crop protection, emergency planning, harvest delay decisions, livestock safety"
            }
        except Exception as e:
            return {
                "tool": "get_weather_alerts",
                "success": False,
                "error": str(e),
                "location": {"lat": lat, "lon": lon}
            }


# Global weather agent instance
weather_agent = WeatherAgent()
