-- Fix language column size to accommodate full language names
-- The current VARCHAR(5) is too small for language names like 'assamese', 'bengali', etc.

-- Increase the size of the language column to accommodate full language names
ALTER TABLE user_profiles 
ALTER COLUMN language TYPE VARCHAR(20);

-- Update the comment to reflect the change
COMMENT ON COLUMN user_profiles.language IS 'User preferred language name (e.g., english, marathi, hindi, assamese, bengali)';

-- No need to update existing data as the column just got larger
