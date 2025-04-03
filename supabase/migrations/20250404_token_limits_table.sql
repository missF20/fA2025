-- Migration: Create token_limits table for token usage tracking
-- Description: This creates a table to store token usage limits for each user

-- Create the token_limits table if it doesn't exist
CREATE TABLE IF NOT EXISTS token_limits (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    model TEXT DEFAULT NULL,
    token_limit INTEGER DEFAULT 0,
    UNIQUE (user_id, model)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS token_limits_user_id_idx ON token_limits(user_id);

-- Apply RLS policies to the token_limits table
ALTER TABLE token_limits ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist to avoid duplication errors
DROP POLICY IF EXISTS user_token_limits_policy ON token_limits;
DROP POLICY IF EXISTS user_token_limits_update_policy ON token_limits;
DROP POLICY IF EXISTS admin_token_limits_policy ON token_limits;

-- Policy: Users can see their own token limits
CREATE POLICY user_token_limits_policy ON token_limits
    FOR SELECT
    USING (user_id::text = auth.uid()::text);

-- Policy: Users can update their own token limits
CREATE POLICY user_token_limits_update_policy ON token_limits
    FOR UPDATE
    USING (user_id::text = auth.uid()::text);

-- Policy: Admin can manage all token limits
CREATE POLICY admin_token_limits_policy ON token_limits
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM admin_users 
            WHERE admin_users.user_id::text = auth.uid()::text
        )
    );