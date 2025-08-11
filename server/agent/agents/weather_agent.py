from __future__ import annotations
from typing import Any, Dict
import time
import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_weather(lat: float, lon: float, days: int = 3, units: str = "metric") -> Dict[str, Any]:
    start = time.time()
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
        ],
        "timezone": "auto",
        "forecast_days": days,
    }
    if units == "imperial":
        params["temperature_unit"] = "fahrenheit"
        params["wind_speed_unit"] = "mph"
    try:
        r = requests.get(OPEN_METEO_URL, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {
            "lat": lat,
            "lon": lon,
            "days": days,
            "units": units,
            "error": str(e),
            "sources": [{"title": "Open-Meteo Forecast", "url": OPEN_METEO_URL}],
        }
    latency = int((time.time() - start) * 1000)

    # Normalize
    daily = data.get("daily", {})
    out = {
        "lat": lat,
        "lon": lon,
        "days": days,
        "units": units,
        "series": {
            "date": daily.get("time", []),
            "tmax": daily.get("temperature_2m_max", []),
            "tmin": daily.get("temperature_2m_min", []),
            "precip": daily.get("precipitation_sum", []),
            "wind_max": daily.get("wind_speed_10m_max", []),
        },
        "sources": [
            {
                "title": "Open-Meteo Forecast",
                "url": r.url,
            }
        ],
        "fetched_at": int(time.time()),
        "latency_ms": latency,
        "confidence": 0.9,
    }
    return out
