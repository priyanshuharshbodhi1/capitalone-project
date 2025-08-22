/*
  # Fix Alert System - Remove Broken Webhook Trigger
  
  This migration fixes the alert system by:
  1. Removing the broken webhook trigger that uses pg_net
  2. Ensuring alerts are created properly by the threshold trigger
  3. Making alerts accessible to users via RLS
  4. Adding debugging capabilities
*/

-- Drop the broken webhook trigger that uses pg_net
DROP TRIGGER IF EXISTS alert_webhook_trigger ON alerts;
DROP FUNCTION IF EXISTS send_alert_webhook();

-- Ensure the threshold checking trigger is working properly
-- First, let's see what triggers exist
DO $$
BEGIN
  RAISE NOTICE 'Checking existing triggers on sensor_data table...';
END $$;

-- Check if the threshold trigger function exists and works properly
CREATE OR REPLACE FUNCTION check_sensor_thresholds()
RETURNS TRIGGER AS $$
DECLARE
  threshold_record RECORD;
  alert_message TEXT;
  current_val NUMERIC;
BEGIN
  -- Log that the trigger is being executed
  RAISE NOTICE 'Threshold trigger fired for device: %, timestamp: %', NEW.device_id, NEW.timestamp;
  
  -- Check each threshold for this device
  FOR threshold_record IN 
    SELECT * FROM thresholds 
    WHERE device_id = NEW.device_id AND is_active = true
  LOOP
    -- Get the current value for this parameter
    CASE threshold_record.parameter
      WHEN 'atmo_temp' THEN current_val := NEW.atmo_temp;
      WHEN 'humidity' THEN current_val := NEW.humidity;
      WHEN 'light' THEN current_val := NEW.light;
      WHEN 'soil_temp' THEN current_val := NEW.soil_temp;
      WHEN 'moisture' THEN current_val := NEW.moisture;
      WHEN 'ec' THEN current_val := NEW.ec;
      WHEN 'ph' THEN current_val := NEW.ph;
      WHEN 'nitrogen' THEN current_val := NEW.nitrogen;
      WHEN 'phosphorus' THEN current_val := NEW.phosphorus;
      WHEN 'potassium' THEN current_val := NEW.potassium;
      ELSE CONTINUE;
    END CASE;

    -- Skip if value is null
    IF current_val IS NULL THEN
      CONTINUE;
    END IF;

    -- Check if value is outside threshold range
    IF (threshold_record.min_value IS NOT NULL AND current_val < threshold_record.min_value) OR
       (threshold_record.max_value IS NOT NULL AND current_val > threshold_record.max_value) THEN
      
      -- Create alert message
      alert_message := format('Alert: %s is %s. Current value: %s. Threshold: %s - %s',
        threshold_record.parameter,
        CASE 
          WHEN current_val < threshold_record.min_value THEN 'below minimum'
          ELSE 'above maximum'
        END,
        current_val,
        COALESCE(threshold_record.min_value::text, 'N/A'),
        COALESCE(threshold_record.max_value::text, 'N/A')
      );

      -- Log the alert creation
      RAISE NOTICE 'Creating alert for %: % (value: %, min: %, max: %)', 
        threshold_record.parameter, alert_message, current_val, 
        threshold_record.min_value, threshold_record.max_value;

      -- Insert alert
      INSERT INTO alerts (
        device_id, user_id, parameter, current_value,
        threshold_min, threshold_max, alert_type, message
      ) VALUES (
        NEW.device_id, NEW.user_id, threshold_record.parameter, current_val,
        threshold_record.min_value, threshold_record.max_value,
        CASE 
          WHEN threshold_record.alert_email AND threshold_record.alert_sms THEN 'both'
          WHEN threshold_record.alert_sms THEN 'sms'
          ELSE 'email'
        END,
        alert_message
      );
      
      RAISE NOTICE 'Alert inserted for %', threshold_record.parameter;
    END IF;
  END LOOP;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Recreate the trigger
DROP TRIGGER IF EXISTS check_thresholds_trigger ON sensor_data;
CREATE TRIGGER check_thresholds_trigger
  AFTER INSERT ON sensor_data
  FOR EACH ROW EXECUTE FUNCTION check_sensor_thresholds();

-- Fix RLS policies for alerts - ensure users can see their own alerts
DROP POLICY IF EXISTS "Users can view own alerts" ON alerts;
CREATE POLICY "Users can view own alerts"
  ON alerts FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

-- Also allow service role to read alerts (for debugging)
DROP POLICY IF EXISTS "Service role can read alerts" ON alerts;
CREATE POLICY "Service role can read alerts"
  ON alerts FOR SELECT
  TO service_role
  USING (true);

-- Create a simple alert notification function that doesn't use pg_net
CREATE OR REPLACE FUNCTION notify_alert_created()
RETURNS TRIGGER AS $$
BEGIN
  -- Just log that an alert was created - external services can poll for new alerts
  RAISE NOTICE 'New alert created: ID=%, Parameter=%, Value=%, Device=%', 
    NEW.id, NEW.parameter, NEW.current_value, NEW.device_id;
  
  -- You can add additional notification logic here that doesn't require pg_net
  -- For now, we'll use a simpler approach where external services poll for unsent alerts
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for alert notifications
CREATE TRIGGER alert_notification_trigger
  AFTER INSERT ON alerts
  FOR EACH ROW
  EXECUTE FUNCTION notify_alert_created();

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION check_sensor_thresholds() TO authenticated;
GRANT EXECUTE ON FUNCTION check_sensor_thresholds() TO service_role;
GRANT EXECUTE ON FUNCTION notify_alert_created() TO authenticated;
GRANT EXECUTE ON FUNCTION notify_alert_created() TO service_role;

-- Create a helpful view for debugging alerts
CREATE OR REPLACE VIEW alert_debug AS
SELECT 
  a.id,
  a.device_id,
  d.device_name,
  a.parameter,
  a.current_value,
  a.threshold_min,
  a.threshold_max,
  a.message,
  a.is_sent,
  a.created_at,
  -- Show which direction the violation was
  CASE 
    WHEN a.current_value < a.threshold_min THEN 'BELOW_MIN'
    WHEN a.current_value > a.threshold_max THEN 'ABOVE_MAX'
    ELSE 'WITHIN_RANGE'
  END as violation_type
FROM alerts a
LEFT JOIN devices d ON a.device_id = d.device_id
ORDER BY a.created_at DESC;

-- Grant access to the debug view
GRANT SELECT ON alert_debug TO authenticated;
GRANT SELECT ON alert_debug TO service_role;

-- Add comments for documentation
COMMENT ON FUNCTION check_sensor_thresholds() IS 'Enhanced threshold checking with proper logging';
COMMENT ON FUNCTION notify_alert_created() IS 'Simple alert notification without pg_net dependency';
COMMENT ON VIEW alert_debug IS 'Debug view showing alert details with violation types';
COMMENT ON TRIGGER check_thresholds_trigger ON sensor_data IS 'Trigger to check thresholds and create alerts';
COMMENT ON TRIGGER alert_notification_trigger ON alerts IS 'Trigger to notify when alerts are created';
