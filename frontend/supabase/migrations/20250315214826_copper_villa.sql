/*
  # Complete Database Cleanup

  1. Actions
    - Drop all existing tables
    - Drop all functions and triggers
    - Drop all policies
    - Remove all data
*/

-- Disable row level security temporarily to allow cleanup
ALTER TABLE IF EXISTS public.messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.conversations DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.responses DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.tasks DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.interactions DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.knowledge_files DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.user_subscriptions DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.admin_users DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.subscription_tiers DISABLE ROW LEVEL SECURITY;

-- Drop all tables in correct order to handle dependencies
DROP TABLE IF EXISTS public.messages CASCADE;
DROP TABLE IF EXISTS public.conversations CASCADE;
DROP TABLE IF EXISTS public.responses CASCADE;
DROP TABLE IF EXISTS public.tasks CASCADE;
DROP TABLE IF EXISTS public.interactions CASCADE;
DROP TABLE IF EXISTS public.knowledge_files CASCADE;
DROP TABLE IF EXISTS public.user_subscriptions CASCADE;
DROP TABLE IF EXISTS public.admin_users CASCADE;
DROP TABLE IF EXISTS public.profiles CASCADE;
DROP TABLE IF EXISTS public.subscription_tiers CASCADE;

-- Drop any remaining functions and triggers
DROP FUNCTION IF EXISTS public.handle_new_user() CASCADE;

-- Drop any custom types if they exist
DO $$ 
DECLARE 
    type_name text;
BEGIN 
    FOR type_name IN (SELECT t.typname 
                      FROM pg_type t 
                      JOIN pg_namespace n ON t.typnamespace = n.oid 
                      WHERE n.nspname = 'public') 
    LOOP
        EXECUTE 'DROP TYPE IF EXISTS public.' || type_name || ' CASCADE;';
    END LOOP;
END $$;