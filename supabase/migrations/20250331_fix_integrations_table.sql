-- Migration to fix the integration_configs table

-- Check if the table exists
DO $$
BEGIN
    -- Ensure extension is available for UUID generation
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    -- Check if integrations_config table exists (wrong name)
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'integrations_config') THEN
        -- Rename integrations_config to integration_configs if it exists
        ALTER TABLE IF EXISTS public.integrations_config RENAME TO integration_configs;
        RAISE NOTICE 'Renamed table integrations_config to integration_configs';
    END IF;

    -- Create the table if it doesn't exist
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'integration_configs') THEN
        -- Create the correctly named table if it doesn't exist
        CREATE TABLE public.integration_configs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL,
            integration_type TEXT NOT NULL,
            config JSONB NOT NULL DEFAULT '{}'::jsonb,
            status TEXT NOT NULL DEFAULT 'pending',
            date_created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            date_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, integration_type)
        );
        
        COMMENT ON TABLE public.integration_configs IS 'Stores integration configurations for users';
        RAISE NOTICE 'Created table integration_configs';
    END IF;
    
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