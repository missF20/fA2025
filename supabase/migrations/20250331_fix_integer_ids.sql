-- Migration to fix integer IDs for the integration_configs table

-- Check if the table exists and make schema modifications if needed
DO $$
BEGIN
    -- Check if integration_configs table exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'integration_configs') THEN
        -- Check ID column type and alter it if needed
        IF EXISTS (
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'integration_configs' 
            AND column_name = 'id' 
            AND data_type = 'uuid'
        ) THEN
            -- Create a temporary column for integer IDs
            ALTER TABLE public.integration_configs ADD COLUMN temp_id SERIAL;
            
            -- Update sequence if needed
            ALTER SEQUENCE integration_configs_temp_id_seq RESTART WITH 1;
            
            -- Make a backup of the data 
            CREATE TEMPORARY TABLE integration_configs_backup AS
            SELECT * FROM public.integration_configs;
            
            -- Drop primary key constraint
            ALTER TABLE public.integration_configs DROP CONSTRAINT IF EXISTS integration_configs_pkey;
            
            -- Alter user_id column type from UUID to INTEGER where appropriate
            -- Only attempt this if needed
            IF EXISTS (
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'integration_configs' 
                AND column_name = 'user_id' 
                AND data_type = 'uuid'
            ) THEN
                -- Drop the existing foreign key constraints if any
                DO $inner$
                DECLARE
                    fk_constraint_name TEXT;
                BEGIN
                    SELECT constraint_name INTO fk_constraint_name
                    FROM information_schema.table_constraints
                    WHERE table_schema = 'public'
                    AND table_name = 'integration_configs'
                    AND constraint_type = 'FOREIGN KEY';
                    
                    IF FOUND THEN
                        EXECUTE 'ALTER TABLE public.integration_configs DROP CONSTRAINT IF EXISTS ' || fk_constraint_name;
                    END IF;
                END $inner$;
                
                -- Alter user_id column to integer
                ALTER TABLE public.integration_configs ALTER COLUMN user_id TYPE INTEGER USING (user_id::text)::integer;
            END IF;
            
            -- Drop the UUID ID column and rename temp_id to id
            ALTER TABLE public.integration_configs DROP COLUMN id;
            ALTER TABLE public.integration_configs RENAME COLUMN temp_id TO id;
            
            -- Add primary key constraint
            ALTER TABLE public.integration_configs ADD PRIMARY KEY (id);
            
            -- Update unique constraint
            ALTER TABLE public.integration_configs DROP CONSTRAINT IF EXISTS integration_configs_user_id_integration_type_key;
            ALTER TABLE public.integration_configs ADD CONSTRAINT integration_configs_user_id_integration_type_key UNIQUE (user_id, integration_type);
            
            RAISE NOTICE 'Modified integration_configs table to use integer IDs';
        END IF;
    END IF;
END
$$;

-- Update or create the function to get integration counts
CREATE OR REPLACE FUNCTION get_integration_counts(table_name text)
RETURNS TABLE (integration_type text, count bigint) 
AS $$
BEGIN
    RETURN QUERY EXECUTE 'SELECT integration_type, COUNT(*) as count FROM ' || table_name || ' GROUP BY integration_type';
END;
$$ LANGUAGE plpgsql;