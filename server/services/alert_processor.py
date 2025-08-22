"""
Alert Processing Service

This service runs periodically to:
1. Check for unsent alerts in the database
2. Send them via the alert-webhook edge function
3. Mark them as sent

Run this as a background service or cron job.
"""

import asyncio
import logging
import os
import httpx
from datetime import datetime
from typing import List, Dict, Any
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertProcessor:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL', '')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
        self.webhook_url = f"{self.supabase_url}/functions/v1/alert-webhook"
        
        if not self.supabase_url or not self.supabase_service_key:
            raise ValueError("Missing required environment variables: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
    
    async def get_unsent_alerts(self) -> List[Dict[str, Any]]:
        """Fetch all unsent alerts from the database"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/alert_summary",
                    headers={
                        "Authorization": f"Bearer {self.supabase_service_key}",
                        "apikey": self.supabase_service_key,
                        "Content-Type": "application/json"
                    },
                    params={
                        "is_sent": "eq.false",
                        "order": "created_at.desc"
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch unsent alerts: {e}")
            return []
    
    async def send_alert_webhook(self, alert: Dict[str, Any]) -> bool:
        """Send a single alert via webhook"""
        try:
            # Format the alert payload similar to the original webhook format
            payload = {
                "alert": {
                    "id": alert["id"],
                    "device_id": alert["device_id"],
                    "user_id": alert.get("user_id"),
                    "parameter": alert["parameter"],
                    "current_value": float(alert["current_value"]),
                    "threshold_min": float(alert["threshold_min"]) if alert["threshold_min"] else None,
                    "threshold_max": float(alert["threshold_max"]) if alert["threshold_max"] else None,
                    "alert_type": alert.get("alert_type", "email"),
                    "message": alert["message"],
                    "created_at": alert["created_at"]
                },
                "device": {
                    "name": alert.get("device_name", "Unknown Device"),
                    "location": alert.get("location"),
                    "type": "ESP32_SENSOR_NODE"
                },
                "user": {
                    "name": alert.get("user_name", "Unknown User"),
                    "phone": alert.get("user_phone"),
                    "email": alert.get("user_email")
                },
                "timestamp": datetime.utcnow().isoformat(),
                "severity": self._determine_severity(alert)
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.webhook_url,
                    headers={
                        "Authorization": f"Bearer {self.supabase_service_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                response.raise_for_status()
                logger.info(f"Successfully sent alert {alert['id']}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send alert {alert['id']}: {e}")
            return False
    
    def _determine_severity(self, alert: Dict[str, Any]) -> str:
        """Determine alert severity based on threshold violation"""
        current_val = float(alert["current_value"])
        threshold_min = float(alert["threshold_min"]) if alert["threshold_min"] else None
        threshold_max = float(alert["threshold_max"]) if alert["threshold_max"] else None
        
        if threshold_min and current_val < threshold_min:
            return "LOW"
        elif threshold_max and current_val > threshold_max:
            return "HIGH"
        else:
            return "NORMAL"
    
    async def mark_alert_as_sent(self, alert_id: str) -> bool:
        """Mark an alert as sent in the database"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.supabase_url}/rest/v1/alerts",
                    headers={
                        "Authorization": f"Bearer {self.supabase_service_key}",
                        "apikey": self.supabase_service_key,
                        "Content-Type": "application/json"
                    },
                    params={"id": f"eq.{alert_id}"},
                    json={
                        "is_sent": True,
                        "sent_at": datetime.utcnow().isoformat()
                    }
                )
                response.raise_for_status()
                logger.info(f"Marked alert {alert_id} as sent")
                return True
        except Exception as e:
            logger.error(f"Failed to mark alert {alert_id} as sent: {e}")
            return False
    
    async def process_alerts(self) -> None:
        """Main processing loop"""
        logger.info("🔍 Checking for unsent alerts...")
        
        unsent_alerts = await self.get_unsent_alerts()
        if not unsent_alerts:
            logger.info("✅ No unsent alerts found")
            return
        
        logger.info(f"📬 Found {len(unsent_alerts)} unsent alerts")
        
        success_count = 0
        for alert in unsent_alerts:
            if await self.send_alert_webhook(alert):
                if await self.mark_alert_as_sent(alert["id"]):
                    success_count += 1
                await asyncio.sleep(1)  # Rate limiting
        
        logger.info(f"✅ Successfully processed {success_count}/{len(unsent_alerts)} alerts")
    
    async def run_continuously(self, interval_seconds: int = 30):
        """Run the alert processor continuously"""
        logger.info(f"🚀 Starting alert processor (checking every {interval_seconds}s)")
        
        while True:
            try:
                await self.process_alerts()
            except Exception as e:
                logger.error(f"❌ Error in alert processing loop: {e}")
            
            await asyncio.sleep(interval_seconds)

async def main():
    processor = AlertProcessor()
    
    # Run once and exit
    await processor.process_alerts()

if __name__ == "__main__":
    asyncio.run(main())
