-- Migration: Create token_usage table for tracking AI service usage
-- Description: This creates a table to store token usage information for each user

-- Create the token_usage table if it doesn't exist
CREATE TABLE IF NOT EXISTS token_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    request_tokens INTEGER NOT NULL,
    response_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    model VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    endpoint VARCHAR(100) NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS token_usage_user_id_idx ON token_usage(user_id);
CREATE INDEX IF NOT EXISTS token_usage_timestamp_idx ON token_usage(timestamp);

-- Apply RLS policies to the token_usage table
ALTER TABLE token_usage ENABLE ROW LEVEL SECURITY;

-- Policy: Users can see their own token usage
CREATE POLICY user_token_usage_policy ON token_usage
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Only auth users can insert their own token usage
CREATE POLICY user_token_usage_insert_policy ON token_usage
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Admin can see all token usage
CREATE POLICY admin_token_usage_policy ON token_usage
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM admin_users 
            WHERE admin_users.user_id = auth.uid()
        )
    );