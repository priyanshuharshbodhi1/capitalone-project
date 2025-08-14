-- Add language column to user_profiles table
-- This migration adds support for storing user language preferences

-- Add language column if it doesn't exist
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS language VARCHAR(5) DEFAULT 'en';

-- Add a comment to document the column
COMMENT ON COLUMN user_profiles.language IS 'User preferred language code (e.g., en, mr, hi)';

-- Create an index for faster queries on language (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_user_profiles_language ON user_profiles(language);

-- Update any existing users to have a default language preference
UPDATE user_profiles 
SET language = 'en' 
WHERE language IS NULL;
