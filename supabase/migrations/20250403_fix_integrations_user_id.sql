-- Migration: Fix user_id datatype in integration_configs table
-- Description: Changes user_id from integer to UUID to match the auth system

-- First, drop all existing policies that depend on user_id
DROP POLICY IF EXISTS "Users can view own integrations" ON integration_configs;
DROP POLICY IF EXISTS "Users can insert own integrations" ON integration_configs;
DROP POLICY IF EXISTS "Users can update own integrations" ON integration_configs;
DROP POLICY IF EXISTS "Users can delete own integrations" ON integration_configs;
DROP POLICY IF EXISTS "select_integration_configs" ON integration_configs;
DROP POLICY IF EXISTS "insert_integration_configs" ON integration_configs;
DROP POLICY IF EXISTS "update_integration_configs" ON integration_configs;
DROP POLICY IF EXISTS "delete_integration_configs" ON integration_configs;

-- Create a new temporary column with UUID type
ALTER TABLE integration_configs ADD COLUMN user_id_uuid UUID;

-- Update the UUID column with data from existing column (converting to UUID)
-- We need to handle the conversion carefully
UPDATE integration_configs 
SET user_id_uuid = 
    CASE 
        -- If the user_id can be converted to text that looks like a UUID, use that
        WHEN length(user_id::text) = 36 AND user_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN 
            user_id::text::uuid
        -- Otherwise, generate a new UUID - note this might break existing relationships
        ELSE 
            gen_random_uuid()
    END;

-- Drop the old column
ALTER TABLE integration_configs DROP COLUMN user_id;

-- Rename the new column to user_id
ALTER TABLE integration_configs RENAME COLUMN user_id_uuid TO user_id;

-- Make user_id NOT NULL again
ALTER TABLE integration_configs ALTER COLUMN user_id SET NOT NULL;

-- Add necessary indices
CREATE INDEX IF NOT EXISTS integration_configs_user_id_idx ON integration_configs(user_id);

-- Create new policies using user_id as UUID
CREATE POLICY "Users can view own integrations" ON integration_configs
    FOR SELECT
    USING (user_id::text = auth.uid()::text);

CREATE POLICY "Users can insert own integrations" ON integration_configs
    FOR INSERT
    WITH CHECK (user_id::text = auth.uid()::text);

CREATE POLICY "Users can update own integrations" ON integration_configs
    FOR UPDATE
    USING (user_id::text = auth.uid()::text);

CREATE POLICY "Users can delete own integrations" ON integration_configs
    FOR DELETE
    USING (user_id::text = auth.uid()::text);