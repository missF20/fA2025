-- Migration: Fix token_usage to use UUID instead of integer for user_id
-- Description: This modifies the token_usage table to use UUID type for user_id to be consistent with other tables

-- First let's check if we need to fix the user_id column
DO $$
DECLARE
    column_type text;
BEGIN
    -- Get the current data type of the user_id column
    SELECT data_type INTO column_type 
    FROM information_schema.columns 
    WHERE table_name = 'token_usage' AND column_name = 'user_id';
    
    -- If the column is integer, we need to convert it to UUID
    IF column_type = 'integer' THEN
        -- First remove any dependencies (foreign keys, etc.)
        ALTER TABLE token_usage DROP CONSTRAINT IF EXISTS token_usage_user_id_fkey;
        
        -- Drop indexes that depend on user_id
        DROP INDEX IF EXISTS token_usage_user_id_idx;
        
        -- Drop policies that depend on user_id
        DROP POLICY IF EXISTS user_token_usage_policy ON token_usage;
        DROP POLICY IF EXISTS user_token_usage_insert_policy ON token_usage;
        DROP POLICY IF EXISTS admin_token_usage_policy ON token_usage;
        
        -- Now change the column type
        -- Since we're going from int to UUID, we'll recreate the column
        ALTER TABLE token_usage DROP COLUMN user_id;
        ALTER TABLE token_usage ADD COLUMN user_id UUID;
        
        -- Recreate indexes
        CREATE INDEX IF NOT EXISTS token_usage_user_id_idx ON token_usage(user_id);
        
        -- Recreate policies
        -- Policy: Users can see their own token usage
        CREATE POLICY user_token_usage_policy ON token_usage
            FOR SELECT
            USING (user_id::text = auth.uid()::text);
        
        -- Policy: Only auth users can insert their own token usage
        CREATE POLICY user_token_usage_insert_policy ON token_usage
            FOR INSERT
            WITH CHECK (user_id::text = auth.uid()::text);
        
        -- Policy: Admin can see all token usage
        CREATE POLICY admin_token_usage_policy ON token_usage
            FOR ALL
            USING (
                EXISTS (
                    SELECT 1 FROM admin_users 
                    WHERE admin_users.user_id::text = auth.uid()::text
                )
            );
        
        -- Set the user_id to NOT NULL now that we've fixed it
        ALTER TABLE token_usage ALTER COLUMN user_id SET NOT NULL;
    END IF;
END
$$;