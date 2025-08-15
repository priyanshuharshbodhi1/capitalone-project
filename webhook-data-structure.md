# Webhook Data Structure for Zapier

This is the exact JSON structure that gets sent to your Zapier webhook:

```json
{
  "alert": {
    "id": "test-1734307554123",
    "device_id": "esp32_001",
    "user_id": "test-user",
    "parameter": "moisture",
    "current_value": 25,
    "threshold_min": 40,
    "threshold_max": null,
    "alert_type": "threshold",
    "message": "TEST ALERT: Soil moisture critically low - immediate irrigation needed",
    "created_at": "2025-08-15T20:15:54.123Z"
  },
  "device": {
    "name": "ESP32 Sensor Node",
    "location": "Test Farm",
    "type": "IoT Sensor"
  },
  "user": {
    "name": "Test User",
    "phone": "+918605992962",
    "email": "priyanshuqpwp@gmail.com"
  },
  "timestamp": "2025-08-15T20:15:54.123Z",
  "severity": "HIGH"
}
```

## Available Fields for Zapier Mapping:

### Alert Fields:
- `alert id` - Unique alert ID
- `alert device_id` - Device identifier
- `alert user_id` - User ID
- `alert parameter` - What triggered the alert (moisture, temperature, etc.)
- `alert current_value` - Current sensor reading
- `alert threshold_min` - Minimum threshold
- `alert threshold_max` - Maximum threshold
- `alert alert_type` - Type of alert (threshold, ai_recommendation)
- `alert message` - Alert message text
- `alert created_at` - When alert was created

### Device Fields:
- `device name` - Device name
- `device location` - Device location
- `device type` - Device type

### User Fields:
- `user name` - User's name
- `user phone` - User's phone number
- `user email` - User's email address

### Other Fields:
- `timestamp` - Alert timestamp
- `severity` - Alert severity (HIGH, MEDIUM, LOW)
