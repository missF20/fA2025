-- Migration to fix the integration_configs table

-- Check if the table exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'integration_configs') THEN
        -- Table exists, enable RLS
        ALTER TABLE integration_configs ENABLE ROW LEVEL SECURITY;
        
        -- Create policies for the table
        DROP POLICY IF EXISTS select_integration_configs ON integration_configs;
        CREATE POLICY select_integration_configs 
            ON integration_configs
            FOR SELECT 
            USING (user_id::text = auth.uid()::text);
            
        DROP POLICY IF EXISTS insert_integration_configs ON integration_configs;
        CREATE POLICY insert_integration_configs 
            ON integration_configs
            FOR INSERT 
            WITH CHECK (user_id::text = auth.uid()::text);
            
        DROP POLICY IF EXISTS update_integration_configs ON integration_configs;
        CREATE POLICY update_integration_configs 
            ON integration_configs
            FOR UPDATE 
            USING (user_id::text = auth.uid()::text);
            
        DROP POLICY IF EXISTS delete_integration_configs ON integration_configs;
        CREATE POLICY delete_integration_configs 
            ON integration_configs
            FOR DELETE 
            USING (user_id::text = auth.uid()::text);
            
        -- Create trigger function to set user_id if not provided
        CREATE OR REPLACE FUNCTION set_auth_user_id()
        RETURNS TRIGGER AS $trigger_func$
        BEGIN
          IF NEW.user_id IS NULL THEN
            NEW.user_id = auth.uid();
          END IF;
          RETURN NEW;
        END;
        $trigger_func$ LANGUAGE plpgsql SECURITY DEFINER;
        
        -- Create trigger to set user_id
        DROP TRIGGER IF EXISTS set_integrations_config_user_id ON integration_configs;
        CREATE TRIGGER set_integrations_config_user_id
          BEFORE INSERT ON integration_configs
          FOR EACH ROW EXECUTE FUNCTION set_auth_user_id();
    END IF;
END
$$;