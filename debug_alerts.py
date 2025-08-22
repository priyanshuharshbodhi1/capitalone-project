#!/usr/bin/env python3
"""
Debug Alert System using Supabase API

This script connects to your Supabase database via the REST API
to check the current state of the alert system.
"""

import os
import json
import asyncio
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Installing...")
    os.system("pip install httpx")
    import httpx

# Load environment variables
def load_env():
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        return {}
    
    env_vars = {}
    for line in env_file.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            env_vars[key.strip()] = value.strip()
    return env_vars

async def check_alerts_state():
    """Check the current state of alerts in the database"""
    env = load_env()
    
    supabase_url = env.get('VITE_SUPABASE_URL', '').replace('https://', '')
    if not supabase_url:
        print("❌ VITE_SUPABASE_URL not found in .env")
        return
    
    supabase_url = f"https://{supabase_url}"
    service_key = env.get('VITE_SUPABASE_SERVICE_ROLE_KEY') or env.get('SUPABASE_SERVICE_ROLE_KEY')
    
    if not service_key:
        print("❌ Service role key not found in .env")
        print("Looking for: VITE_SUPABASE_SERVICE_ROLE_KEY or SUPABASE_SERVICE_ROLE_KEY")
        return
    
    headers = {
        "Authorization": f"Bearer {service_key}",
        "apikey": service_key,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        print("🔍 Checking Alert System State...")
        print("=" * 50)
        
        # 1. Check alerts count
        try:
            response = await client.get(
                f"{supabase_url}/rest/v1/alerts",
                headers=headers,
                params={"select": "count"}
            )
            if response.status_code == 200:
                alerts = response.json()
                print(f"📊 Total alerts in database: {len(alerts)}")
            else:
                print(f"❌ Failed to get alerts: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error checking alerts: {e}")
        
        # 2. Check recent alerts
        try:
            response = await client.get(
                f"{supabase_url}/rest/v1/alerts",
                headers=headers,
                params={
                    "select": "id,device_id,parameter,current_value,threshold_min,threshold_max,message,is_sent,created_at",
                    "order": "created_at.desc",
                    "limit": "5"
                }
            )
            if response.status_code == 200:
                alerts = response.json()
                print(f"\n📋 Recent alerts ({len(alerts)}):")
                for alert in alerts:
                    status = "✅ Sent" if alert['is_sent'] else "⏳ Pending"
                    print(f"  - {alert['parameter']}: {alert['current_value']} ({status}) - {alert['created_at']}")
            else:
                print(f"❌ Failed to get recent alerts: {response.status_code}")
        except Exception as e:
            print(f"❌ Error checking recent alerts: {e}")
        
        # 3. Check thresholds
        try:
            response = await client.get(
                f"{supabase_url}/rest/v1/thresholds",
                headers=headers,
                params={
                    "select": "parameter,min_value,max_value,is_active,alert_email,alert_sms",
                    "is_active": "eq.true"
                }
            )
            if response.status_code == 200:
                thresholds = response.json()
                print(f"\n⚙️ Active thresholds ({len(thresholds)}):")
                for t in thresholds:
                    print(f"  - {t['parameter']}: {t['min_value']} - {t['max_value']} (Email: {t['alert_email']}, SMS: {t['alert_sms']})")
            else:
                print(f"❌ Failed to get thresholds: {response.status_code}")
        except Exception as e:
            print(f"❌ Error checking thresholds: {e}")
        
        # 4. Check recent sensor data
        try:
            response = await client.get(
                f"{supabase_url}/rest/v1/sensor_data",
                headers=headers,
                params={
                    "select": "device_id,atmo_temp,humidity,moisture,ph,ec,timestamp",
                    "order": "timestamp.desc",
                    "limit": "3"
                }
            )
            if response.status_code == 200:
                data = response.json()
                print(f"\n📊 Recent sensor data ({len(data)}):")
                for d in data:
                    print(f"  - {d['device_id']}: temp={d['atmo_temp']}, moisture={d['moisture']}, ph={d['ph']} - {d['timestamp']}")
            else:
                print(f"❌ Failed to get sensor data: {response.status_code}")
        except Exception as e:
            print(f"❌ Error checking sensor data: {e}")
        
        # 5. Check devices
        try:
            response = await client.get(
                f"{supabase_url}/rest/v1/devices",
                headers=headers,
                params={"select": "device_id,device_name,is_active,last_seen"}
            )
            if response.status_code == 200:
                devices = response.json()
                print(f"\n📱 Devices ({len(devices)}):")
                for d in devices:
                    status = "🟢 Active" if d['is_active'] else "🔴 Inactive"
                    print(f"  - {d['device_name']} ({d['device_id']}): {status} - Last seen: {d['last_seen']}")
            else:
                print(f"❌ Failed to get devices: {response.status_code}")
        except Exception as e:
            print(f"❌ Error checking devices: {e}")

async def test_threshold_violation():
    """Test if threshold violations trigger alerts"""
    env = load_env()
    supabase_url = env.get('VITE_SUPABASE_URL', '')
    service_key = env.get('VITE_SUPABASE_SERVICE_ROLE_KEY') or env.get('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not service_key:
        print("❌ Missing Supabase configuration")
        return
    
    print("\n🧪 Testing Threshold Violation...")
    print("=" * 50)
    print("To test the alert system:")
    print("1. Go to your MockSensor page")
    print("2. Set these values to trigger alerts:")
    print("   - moisture: 5 (should trigger low moisture alert)")
    print("   - ph: 3.0 (should trigger pH out of range alert)")
    print("   - atmo_temp: 50 (should trigger high temperature alert)")
    print("3. Send the sensor data")
    print("4. Run this script again to see if alerts were created")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        asyncio.run(test_threshold_violation())
    else:
        asyncio.run(check_alerts_state())
