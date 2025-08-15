import { SensorData } from '../types';

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
  checkAlerts(sensorData: SensorData, recommendations?: AIRecommendation[]): AlertPayload[] {
    const alerts: AlertPayload[] = [];
    const timestamp = new Date().toISOString();

    // Check threshold-based alerts
    for (const rule of this.alertRules) {
      const value = sensorData[rule.parameter] as number;
      let shouldAlert = false;

      if (rule.min !== undefined && value < rule.min) {
        shouldAlert = true;
      }
      if (rule.max !== undefined && value > rule.max) {
        shouldAlert = true;
      }

      if (shouldAlert) {
        alerts.push({
          alert: {
            id: `alert_${Date.now()}_${rule.parameter}`,
            device_id: 'esp32_001', // Default device ID
            user_id: 'user_001', // Default user ID
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
            location: 'Farm Location',
            type: 'IoT Sensor',
          },
          user: {
            name: 'Farm Manager',
            phone: '+1234567890', // Configure this
          },
          timestamp,
          severity: rule.severity,
          recommendations: recommendations?.filter(rec => 
            rec.priority === 'high' && rec.actionable
          )
        });
      }
    }

    // Check AI recommendation-based alerts (high priority only)
    if (recommendations) {
      const highPriorityRecs = recommendations.filter(rec => 
        rec.priority === 'high' && rec.actionable && rec.confidence > 80
      );

      for (const rec of highPriorityRecs) {
        alerts.push({
          alert: {
            id: `ai_alert_${Date.now()}_${rec.type}`,
            device_id: 'esp32_001',
            user_id: 'user_001',
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
            location: 'Farm Location',
            type: 'IoT Sensor',
          },
          user: {
            name: 'Farm Manager',
            phone: '+1234567890',
          },
          timestamp,
          severity: 'HIGH',
          recommendations: [rec]
        });
      }
    }

    return alerts;
  }

  // Send alerts to webhook (Zapier)
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
        } else {
          console.error(`❌ Failed to send alert: ${alert.alert.id}`, await response.text());
        }
      } catch (error) {
        console.error(`❌ Error sending alert: ${alert.alert.id}`, error);
      }
    }
  }

  // Process sensor data and send alerts if needed
  async processAlerts(sensorData: SensorData, recommendations?: AIRecommendation[]): Promise<void> {
    const alerts = this.checkAlerts(sensorData, recommendations);
    
    if (alerts.length > 0) {
      console.log(`🔍 AlertService: Found ${alerts.length} alerts to send`);
      await this.sendAlerts(alerts);
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
