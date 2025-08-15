// Test Zapier webhook directly
// Replace YOUR_ZAPIER_WEBHOOK_URL with your actual Zapier webhook URL

const testPayload = {
  alert: {
    id: "test-" + Date.now(),
    device_id: "esp32_001",
    user_id: "test-user",
    parameter: "moisture",
    current_value: 25,
    threshold_min: 40,
    threshold_max: null,
    alert_type: "threshold",
    message: "TEST ALERT: Soil moisture critically low - immediate irrigation needed",
    created_at: new Date().toISOString()
  },
  device: {
    name: "ESP32 Sensor Node",
    location: "Test Farm",
    type: "IoT Sensor"
  },
  user: {
    name: "Test User",
    phone: "+918605992962", // Replace with your actual phone number
    email: "priyanshuqpwp@gmail.com" // Replace with your actual email
  },
  timestamp: new Date().toISOString(),
  severity: "HIGH"
};

async function testZapierWebhook() {
  // Replace this with your actual Zapier webhook URL from Step 1 of your Zap
  const ZAPIER_WEBHOOK_URL = "https://hooks.zapier.com/hooks/catch/24232349/u67i2w3/";
  
  try {
    console.log("🧪 Testing Zapier webhook directly...");
    console.log("📤 Sending payload:", JSON.stringify(testPayload, null, 2));
    
    const response = await fetch(ZAPIER_WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Source': 'EcoBolt-Alert-System',
      },
      body: JSON.stringify(testPayload)
    });

    if (response.ok) {
      const result = await response.text();
      console.log("✅ Zapier webhook test successful!");
      console.log("📋 Response:", result);
      console.log("🔔 Check your phone and email for the test alert!");
    } else {
      console.error("❌ Zapier webhook test failed:", response.status, response.statusText);
      const errorText = await response.text();
      console.error("Error details:", errorText);
    }
  } catch (error) {
    console.error("❌ Error testing Zapier webhook:", error.message);
  }
}

console.log("📋 Instructions:");
console.log("1. Update ZAPIER_WEBHOOK_URL above with your actual webhook URL");
console.log("2. Update phone and email in testPayload");
console.log("3. Run: node test-zapier.js");
console.log("4. Check your phone and email for the test alert");

// Uncomment the line below after updating the webhook URL
testZapierWebhook();
