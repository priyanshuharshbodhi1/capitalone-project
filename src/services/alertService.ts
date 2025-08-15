import { SensorData, User } from '../types';
import { supabaseApi } from './supabaseApi';

interface AlertRule {
  parameter: keyof SensorData;
  min?: number;
  max?: number;
  severity: 'LOW' | 'HIGH' | 'NORMAL';
  message: string;
}

interface AIRecommendation {
  type: 'practice' | 'fertilizer' | 'crop' | 'insight';
  title: string;
  description: string;
  confidence: number;
  priority: 'high' | 'medium' | 'low';
  actionable: boolean;
  reasoning: string;
}

interface AlertPayload {
  alert: {
    id: string;
    device_id: string;
    user_id: string;
    parameter: string;
    current_value: number;
    threshold_min: number | null;
    threshold_max: number | null;
    alert_type: string;
    message: string;
    created_at: string;
  };
  device: {
    name: string;
    location: string | null;
    type: string;
  };
  user: {
    name: string;
    phone: string | null;
    email: string | null;
  };
  timestamp: string;
  severity: 'LOW' | 'HIGH' | 'NORMAL';
  recommendations?: AIRecommendation[];
}

class AlertService {
  private supabaseUrl: string;
  private supabaseAnonKey: string;
  private webhookUrl: string;

  // Default alert rules based on your fallback thresholds
  private alertRules: AlertRule[] = [
    {
      parameter: 'moisture',
      min: 40,
      severity: 'HIGH',
      message: 'Soil moisture critically low - immediate irrigation needed'
    },
    {
      parameter: 'ph',
      min: 6.0,
      max: 7.5,
      severity: 'HIGH',
      message: 'Soil pH outside optimal range - adjustment required'
    },
    {
      parameter: 'atmoTemp',
      max: 35,
      severity: 'HIGH',
      message: 'High temperature detected - heat stress risk'
    },
    {
      parameter: 'n',
      min: 30,
      severity: 'LOW',
      message: 'Nitrogen levels low - fertilizer application recommended'
    },
    {
      parameter: 'light',
      min: 300,
      severity: 'LOW',
      message: 'Light levels below optimal - supplementation may be needed'
    },
    {
      parameter: 'ec',
      max: 2.5,
      severity: 'HIGH',
      message: 'High salt content detected - soil flushing required'
    }
  ];

  constructor() {
    this.supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
    this.supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';
    this.webhookUrl = `${this.supabaseUrl}/functions/v1/alert-webhook`;
  }

  // Check sensor data against alert rules
  async processAlerts(sensorData: SensorData, user: User): Promise<AlertPayload[]> {
    const alerts: AlertPayload[] = [];
    const timestamp = new Date().toISOString();

    // Get or create device for this user
    const deviceId = await this.getOrCreateDevice(user.id);

    // Check threshold-based alerts
    for (const rule of this.alertRules) {
      const value = sensorData[rule.parameter];
      if (value === undefined || value === null) continue;

      let shouldAlert = false;
      if (rule.min !== undefined && value < rule.min) {
        shouldAlert = true;
      }
      if (rule.max !== undefined && value > rule.max) {
        shouldAlert = true;
      }

      if (shouldAlert) {
        // Store alert in database (let database generate UUID)
        const alertData = {
          device_id: deviceId,
          user_id: user.id,
          parameter: rule.parameter,
          current_value: value,
          threshold_min: rule.min || null,
          threshold_max: rule.max || null,
          alert_type: 'threshold',
          message: rule.message,
          created_at: timestamp,
          is_sent: false
        };
        
        const alertId = await this.storeAlert(alertData);

        alerts.push({
          alert: {
            id: alertId,
            device_id: deviceId,
            user_id: user.id,
            parameter: rule.parameter,
            current_value: value,
            threshold_min: rule.min || null,
            threshold_max: rule.max || null,
            alert_type: 'threshold',
            message: rule.message,
            created_at: timestamp,
          },
          device: {
            name: 'ESP32 Sensor Node',
            location: user.location || 'Farm Location',
            type: 'IoT Sensor',
          },
          user: {
            name: user.name,
            phone: user.phone || null,
            email: user.email || null,
          },
          timestamp,
          severity: rule.severity,
        });
      }
    }

    return alerts;
  }

  // Get or create device for user
  private async getOrCreateDevice(userId: string): Promise<string> {
    try {
      // First try to find existing device for this user
      const { data: existingDevices } = await supabaseApi.getDevices(userId);
      
      if (existingDevices && existingDevices.length > 0) {
        return existingDevices[0].device_id;
      }

      // If no device exists, create one
      const deviceData = {
        device_id: `esp32_${userId.slice(-8)}`, // Use last 8 chars of user ID
        user_id: userId,
        device_name: 'ESP32 Sensor Node',
        device_type: 'ESP32_SENSOR_NODE',
        location: 'Farm Location',
        is_active: true,
        last_seen: new Date().toISOString()
      };

      const newDevice = await supabaseApi.createDevice(deviceData);
      return newDevice.device_id;
    } catch (error) {
      console.error('❌ Error getting/creating device:', error);
      // Fallback to a default device ID pattern
      return `esp32_${userId.slice(-8)}`;
    }
  }

  // Process AI recommendations and create alerts
  async processAIRecommendations(recommendations: AIRecommendation[], user: User): Promise<AlertPayload[]> {
    const alerts: AlertPayload[] = [];
    const timestamp = new Date().toISOString();

    // Get or create device for this user
    const deviceId = await this.getOrCreateDevice(user.id);

    // Check AI recommendation-based alerts (high priority only)
    if (recommendations) {
      const highPriorityRecs = recommendations.filter(rec => 
        rec.priority === 'high' && rec.actionable && rec.confidence > 80
      );

      for (const rec of highPriorityRecs) {
        // Store alert in database (let database generate UUID)
        const alertData = {
          device_id: deviceId,
          user_id: user.id,
          parameter: rec.type,
          current_value: rec.confidence,
          threshold_min: null,
          threshold_max: null,
          alert_type: 'ai_recommendation',
          message: `AI Alert: ${rec.title} - ${rec.description}`,
          created_at: timestamp,
          is_sent: false
        };
        
        const alertId = await this.storeAlert(alertData);

        alerts.push({
          alert: {
            id: alertId,
            device_id: deviceId,
            user_id: user.id,
            parameter: rec.type,
            current_value: rec.confidence,
            threshold_min: null,
            threshold_max: null,
            alert_type: 'ai_recommendation',
            message: `AI Alert: ${rec.title} - ${rec.description}`,
            created_at: timestamp,
          },
          device: {
            name: 'ESP32 Sensor Node',
            location: user.location || 'Farm Location',
            type: 'IoT Sensor',
          },
          user: {
            name: user.name,
            phone: user.phone || null,
            email: user.email || null,
          },
          timestamp,
          severity: 'HIGH',
          recommendations: [rec]
        });
      }
    }

    return alerts;
  }

  // Store alert in database
  async storeAlert(alertData: {
    device_id: string;
    user_id: string;
    parameter: string;
    current_value: number;
    threshold_min: number | null;
    threshold_max: number | null;
    alert_type: string;
    message: string;
    created_at: string;
    is_sent: boolean;
  }): Promise<string> {
    try {
      const alertId = await supabaseApi.createAlert(alertData);
      console.log(`✅ Alert stored in database: ${alertId}`);
      return alertId;
    } catch (error) {
      console.error(`❌ Failed to store alert:`, error);
      throw error;
    }
  }

  // Send alerts to webhook (Zapier) and mark as sent
  async sendAlerts(alerts: AlertPayload[]): Promise<void> {
    if (!alerts.length || !this.supabaseUrl || !this.supabaseAnonKey) {
      return;
    }

    console.log(`🚨 AlertService: Sending ${alerts.length} alerts to webhook`);

    for (const alert of alerts) {
      try {
        const response = await fetch(this.webhookUrl, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.supabaseAnonKey}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(alert),
        });

        if (response.ok) {
          console.log(`✅ Alert sent: ${alert.alert.id}`);
          // Mark alert as sent in database
          await this.markAlertAsSent(alert.alert.id);
        } else {
          console.error(`❌ Failed to send alert: ${alert.alert.id}`, await response.text());
        }
      } catch (error) {
        console.error(`❌ Error sending alert: ${alert.alert.id}`, error);
      }
    }
  }

  // Mark alert as sent in database
  async markAlertAsSent(alertId: string): Promise<void> {
    try {
      await supabaseApi.updateAlertStatus(alertId, true);
      console.log(`✅ Alert marked as sent: ${alertId}`);
    } catch (error) {
      console.error(`❌ Failed to mark alert as sent: ${alertId}`, error);
    }
  }

  // Main method to check alerts and send them
  async checkAndSendAlerts(sensorData: SensorData, user: User, recommendations?: AIRecommendation[]): Promise<void> {
    // Get threshold-based alerts
    const thresholdAlerts = await this.processAlerts(sensorData, user);
    
    // Get AI recommendation alerts if provided
    let aiAlerts: AlertPayload[] = [];
    if (recommendations) {
      aiAlerts = await this.processAIRecommendations(recommendations, user);
    }
    
    const allAlerts = [...thresholdAlerts, ...aiAlerts];
    
    if (allAlerts.length > 0) {
      console.log(`🔍 AlertService: Found ${allAlerts.length} alerts to send`);
      await this.sendAlerts(allAlerts);
    } else {
      console.log('✅ AlertService: No alerts triggered');
    }
  }

  // Check if alert service is configured
  isConfigured(): boolean {
    return !!(this.supabaseUrl && this.supabaseAnonKey);
  }
}

export const alertService = new AlertService();
