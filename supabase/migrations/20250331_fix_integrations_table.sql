-- Fix integrations table name references
-- This migration fixes a typo in the table name references for RLS policies

-- Drop any existing policies that reference "integrations_config" (incorrect)
-- These might not exist, so we'll ignore errors

-- Create a helper function to safely drop objects that may or may not exist
CREATE OR REPLACE FUNCTION drop_object_if_exists(object_type text, object_name text, object_schema text DEFAULT 'public') 
RETURNS void AS $$
DECLARE
    object_exists boolean;
BEGIN
    -- Check if the object exists
    EXECUTE 'SELECT EXISTS (' ||
        'SELECT 1 FROM pg_catalog.pg_' || CASE
            WHEN object_type = 'table' THEN 'class WHERE relname = ' || quote_literal(object_name) || ' AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = ' || quote_literal(object_schema) || ')'
            WHEN object_type = 'function' THEN 'proc WHERE proname = ' || quote_literal(object_name) || ' AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = ' || quote_literal(object_schema) || ')'
            WHEN object_type = 'trigger' THEN 'trigger WHERE tgname = ' || quote_literal(object_name) || ' AND tgrelid = (SELECT oid FROM pg_class WHERE relname = $1 AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = ' || quote_literal(object_schema) || '))'
            WHEN object_type = 'view' THEN 'class WHERE relname = ' || quote_literal(object_name) || ' AND relkind = ''v'' AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = ' || quote_literal(object_schema) || ')'
            WHEN object_type = 'index' THEN 'class WHERE relname = ' || quote_literal(object_name) || ' AND relkind = ''i'' AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = ' || quote_literal(object_schema) || ')'
            ELSE 'class WHERE relname = ' || quote_literal(object_name) || ' AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = ' || quote_literal(object_schema) || ')'
        END || ')' INTO object_exists;

    -- Drop the object if it exists
    IF object_exists THEN
        EXECUTE 'DROP ' || object_type || ' IF EXISTS ' || object_schema || '.' || object_name || CASE WHEN object_type = 'table' THEN ' CASCADE' ELSE '' END;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Attempt to drop policies that might be using the wrong table name
DO $$
BEGIN
    -- Try to drop existing policies, ignoring if they don't exist
    PERFORM drop_object_if_exists('policy', 'Users can view own integrations', 'public');
    PERFORM drop_object_if_exists('policy', 'Users can insert own integrations', 'public');
    PERFORM drop_object_if_exists('policy', 'Users can update own integrations', 'public');
    PERFORM drop_object_if_exists('policy', 'Users can delete own integrations', 'public');
    PERFORM drop_object_if_exists('policy', 'Admins can manage all integrations', 'public');
    
    -- Clean up temporary function
    DROP FUNCTION IF EXISTS drop_object_if_exists(text, text, text);
EXCEPTION 
    WHEN OTHERS THEN
        RAISE NOTICE 'Error dropping policies: %', SQLERRM;
END;
$$;

-- Apply correct policies for integration_configs (with the correct table name)
DO $$
BEGIN
    -- Enable RLS on integration_configs if not already enabled
    ALTER TABLE integration_configs ENABLE ROW LEVEL SECURITY;
    
    -- Create policies with correct table name
    CREATE POLICY "Users can view own integrations" ON integration_configs
      FOR SELECT USING (auth.uid()::text = user_id::text);
    
    CREATE POLICY "Users can insert own integrations" ON integration_configs
      FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);
    
    CREATE POLICY "Users can update own integrations" ON integration_configs
      FOR UPDATE USING (auth.uid()::text = user_id::text);
    
    CREATE POLICY "Users can delete own integrations" ON integration_configs
      FOR DELETE USING (auth.uid()::text = user_id::text);
    
    CREATE POLICY "Admins can manage all integrations" ON integration_configs
      FOR ALL USING (is_admin(auth.uid()));
EXCEPTION 
    WHEN OTHERS THEN
        RAISE NOTICE 'Error creating policies: %', SQLERRM;
END;
$$;

-- Re-create the trigger for setting user_id for integration_configs
DROP TRIGGER IF EXISTS set_integrations_config_user_id ON integration_configs;
CREATE TRIGGER set_integrations_config_user_id
  BEFORE INSERT ON integration_configs
  FOR EACH ROW EXECUTE FUNCTION set_auth_user_id();