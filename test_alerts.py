#!/usr/bin/env python3
"""
Alert System Test Script

This script helps you test the alert system by:
1. Checking database configuration
2. Creating test alerts
3. Verifying alert processing
4. Testing the complete flow

Usage:
    python test_alerts.py --check-setup
    python test_alerts.py --create-test-alert
    python test_alerts.py --process-alerts
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

# Add server directory to path
sys.path.append(str(Path(__file__).parent / "server"))

try:
    from services.alert_processor import AlertProcessor
except ImportError:
    print("❌ Could not import AlertProcessor. Make sure to install dependencies:")
    print("pip install httpx")
    sys.exit(1)

async def check_setup():
    """Check if the alert system is properly configured"""
    print("🔍 Checking alert system setup...")
    
    # Check environment variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file:")
        for var in missing_vars:
            print(f"  {var}=your_value_here")
        return False
    
    print("✅ Environment variables configured")
    
    # Test database connection
    try:
        processor = AlertProcessor()
        alerts = await processor.get_unsent_alerts()
        print(f"✅ Database connection successful. Found {len(alerts)} unsent alerts")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def create_test_alert():
    """Create a test alert to verify the system"""
    print("🧪 Creating test alert...")
    print("Note: This requires you to send sensor data via MockSensor that violates thresholds")
    print("The database trigger should automatically create alerts when thresholds are violated")
    
    processor = AlertProcessor()
    alerts = await processor.get_unsent_alerts()
    
    if alerts:
        print(f"✅ Found {len(alerts)} existing unsent alerts")
        for alert in alerts[:3]:  # Show first 3
            print(f"  - {alert['parameter']}: {alert['current_value']} (created: {alert['created_at']})")
    else:
        print("ℹ️ No unsent alerts found. Try these steps:")
        print("1. Go to MockSensor page")
        print("2. Generate random values that violate thresholds")
        print("3. Or manually set values outside threshold ranges")
        print("4. Send the sensor data")
        print("5. Run this script again")

async def process_alerts():
    """Process any pending alerts"""
    print("📬 Processing pending alerts...")
    
    processor = AlertProcessor()
    await processor.process_alerts()

async def monitor_alerts():
    """Monitor alerts continuously"""
    print("👀 Monitoring alerts continuously (Ctrl+C to stop)...")
    
    processor = AlertProcessor()
    try:
        await processor.run_continuously(interval_seconds=30)
    except KeyboardInterrupt:
        print("\n✅ Monitoring stopped")

def main():
    parser = argparse.ArgumentParser(description="Test and debug alert system")
    parser.add_argument('--check-setup', action='store_true', help='Check system configuration')
    parser.add_argument('--create-test-alert', action='store_true', help='Create test alert')
    parser.add_argument('--process-alerts', action='store_true', help='Process pending alerts')
    parser.add_argument('--monitor', action='store_true', help='Monitor alerts continuously')
    
    args = parser.parse_args()
    
    if args.check_setup:
        asyncio.run(check_setup())
    elif args.create_test_alert:
        asyncio.run(create_test_alert())
    elif args.process_alerts:
        asyncio.run(process_alerts())
    elif args.monitor:
        asyncio.run(monitor_alerts())
    else:
        print("Alert System Test Script")
        print("========================")
        print()
        print("Usage examples:")
        print("  python test_alerts.py --check-setup      # Check configuration")
        print("  python test_alerts.py --create-test-alert # Check for existing alerts")
        print("  python test_alerts.py --process-alerts    # Process pending alerts")
        print("  python test_alerts.py --monitor          # Monitor continuously")
        print()
        print("Debugging workflow:")
        print("1. Run --check-setup to verify configuration")
        print("2. Use MockSensor to create sensor data that violates thresholds")
        print("3. Run --create-test-alert to check if alerts were created")
        print("4. Run --process-alerts to send any pending alerts")
        print("5. Check the dashboard to see if alerts appear")

if __name__ == "__main__":
    main()
