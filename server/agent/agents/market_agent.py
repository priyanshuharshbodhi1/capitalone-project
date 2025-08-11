from __future__ import annotations
from typing import Any, Dict, Optional
import time
import requests
from ...infra.settings import settings

# Simple Agmarknet proxy using data.gov.in. If API key not present, returns demo data.
DATA_GOV_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"  # Agmarknet prices dataset


def fetch_market(commodity: str, state: Optional[str] = None, district: Optional[str] = None, market: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
    start = time.time()
    api_key = settings.datagovin_api_key
    if not api_key:
        # Demo response to keep endpoint working without a key
        return {
            "commodity": commodity,
            "series": [
                {"date": "2025-08-01", "modal_price": 1800},
                {"date": "2025-08-02", "modal_price": 1825},
                {"date": "2025-08-03", "modal_price": 1770},
                {"date": "2025-08-04", "modal_price": 1850},
            ],
            "sources": [
                {"title": "Demo Agmarknet", "url": "https://agmarknet.gov.in/"}
            ],
            "note": "Set DATA_GOV_IN_API_KEY to fetch live prices.",
            "fetched_at": int(time.time()),
            "latency_ms": int((time.time() - start) * 1000),
        }

    params = {
        "api-key": api_key,
        "format": "json",
        "limit": 100,
        "sort": "_id desc",
        "filters[commodity]": commodity,
    }
    if state:
        params["filters[state]"] = state
    if district:
        params["filters[district]"] = district
    if market:
        params["filters[market]"] = market

    r = requests.get(DATA_GOV_URL, params=params, timeout=20)
    r.raise_for_status()
    obj = r.json()
    recs = obj.get("records", [])
    series = [
        {"date": rec.get("arrival_date"), "modal_price": _safe_int(rec.get("modal_price"))}
        for rec in recs
        if rec.get("arrival_date") and rec.get("modal_price")
    ]
    series = list(reversed(series))  # oldest first

    return {
        "commodity": commodity,
        "state": state,
        "district": district,
        "market": market,
        "series": series,
        "stats": _stats(series),
        "sources": [{"title": "Agmarknet via data.gov.in", "url": r.url}],
        "fetched_at": int(time.time()),
        "latency_ms": int((time.time() - start) * 1000),
    }


def _safe_int(x) -> Optional[int]:
    try:
        return int(str(x).split(".")[0])
    except Exception:
        return None


def _stats(series: list[dict[str, Any]]) -> dict[str, Any]:
    vals = [s["modal_price"] for s in series if isinstance(s.get("modal_price"), int)]
    if not vals:
        return {}
    return {
        "min": min(vals),
        "max": max(vals),
        "median": sorted(vals)[len(vals)//2],
        "latest": vals[-1],
        "count": len(vals),
    }
