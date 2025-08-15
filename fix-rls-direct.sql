-- Direct fix for RLS policies - run this in Supabase SQL Editor

-- First, disable RLS temporarily to fix the policies
ALTER TABLE alerts DISABLE ROW LEVEL SECURITY;
ALTER TABLE sensor_data DISABLE ROW LEVEL SECURITY;
ALTER TABLE devices DISABLE ROW LEVEL SECURITY;
ALTER TABLE thresholds DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY;

-- Drop all existing policies
DROP POLICY IF EXISTS "Users can view own alerts" ON alerts;
DROP POLICY IF EXISTS "Service role can manage alerts" ON alerts;
DROP POLICY IF EXISTS "Service role can manage all alerts" ON alerts;
DROP POLICY IF EXISTS "Anon can insert alerts" ON alerts;
DROP POLICY IF EXISTS "Anon can read alerts" ON alerts;
DROP POLICY IF EXISTS "Users can insert own alerts" ON alerts;

-- Create simple, permissive policies
CREATE POLICY "Allow all operations on alerts"
  ON alerts FOR ALL
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow all operations on sensor_data"
  ON sensor_data FOR ALL
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow all operations on devices"
  ON devices FOR ALL
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow all operations on thresholds"
  ON thresholds FOR ALL
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow all operations on user_profiles"
  ON user_profiles FOR ALL
  USING (true)
  WITH CHECK (true);

-- Re-enable RLS with permissive policies
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensor_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE thresholds ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
