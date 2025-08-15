-- Fix RLS policies for alerts table to allow service role and function access

-- Drop existing restrictive policies
DROP POLICY IF EXISTS "Users can view own alerts" ON alerts;
DROP POLICY IF EXISTS "Service role can manage alerts" ON alerts;

-- Create more permissive policies for alerts
CREATE POLICY "Users can view own alerts"
  ON alerts FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own alerts"
  ON alerts FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

-- Allow service role full access (for Edge Functions)
CREATE POLICY "Service role can manage all alerts"
  ON alerts FOR ALL
  TO service_role
  WITH CHECK (true);

-- Allow anon role to insert alerts (for webhook endpoints)
CREATE POLICY "Anon can insert alerts"
  ON alerts FOR INSERT
  TO anon
  WITH CHECK (true);

-- Allow anon role to read alerts (for webhook endpoints)
CREATE POLICY "Anon can read alerts"
  ON alerts FOR SELECT
  TO anon
  USING (true);

-- Fix sensor_data policies to allow anon access for ESP32 devices
CREATE POLICY "Anon can insert sensor data"
  ON sensor_data FOR INSERT
  TO anon
  WITH CHECK (true);

CREATE POLICY "Anon can read sensor data"
  ON sensor_data FOR SELECT
  TO anon
  USING (true);

-- Fix devices table for anon access
CREATE POLICY "Anon can read devices"
  ON devices FOR SELECT
  TO anon
  USING (true);

-- Fix thresholds table for anon access
CREATE POLICY "Anon can read thresholds"
  ON thresholds FOR SELECT
  TO anon
  USING (true);

-- Fix user_profiles for anon access
CREATE POLICY "Anon can read user profiles"
  ON user_profiles FOR SELECT
  TO anon
  USING (true);
