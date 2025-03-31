-- Migration to fix auth schema issues
-- This script creates a PostgreSQL-compatible auth schema similar to Supabase

-- Create auth schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS auth;

-- Create users table in auth schema if it doesn't exist
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(50) DEFAULT 'authenticated',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_sign_in_at TIMESTAMP WITH TIME ZONE,
    raw_app_meta_data JSONB,
    raw_user_meta_data JSONB,
    is_anonymous BOOLEAN DEFAULT false,
    confirmation_token VARCHAR(255),
    confirmed_at TIMESTAMP WITH TIME ZONE,
    confirmation_sent_at TIMESTAMP WITH TIME ZONE,
    recovery_token VARCHAR(255),
    recovery_sent_at TIMESTAMP WITH TIME ZONE,
    email_change_token VARCHAR(255),
    email_change VARCHAR(255),
    email_change_sent_at TIMESTAMP WITH TIME ZONE,
    is_super_admin BOOLEAN DEFAULT false
);

-- Create view to link auth users with local users
CREATE OR REPLACE VIEW user_details AS
SELECT 
    u.id as user_id,
    au.id as auth_id, 
    u.email,
    u.username,
    p.company,
    p.account_setup_complete,
    p.welcome_email_sent,
    au.role as auth_role,
    u.is_admin
FROM 
    users u
LEFT JOIN 
    auth.users au ON u.email = au.email
LEFT JOIN
    profiles p ON u.id = p.user_id;

-- Create function to maintain sync between users tables
CREATE OR REPLACE FUNCTION sync_auth_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Create a corresponding auth.users record if none exists
    IF NOT EXISTS (SELECT 1 FROM auth.users WHERE email = NEW.email) THEN
        INSERT INTO auth.users (email, role, raw_user_meta_data)
        VALUES (
            NEW.email, 
            CASE WHEN NEW.is_admin THEN 'admin' ELSE 'authenticated' END,
            jsonb_build_object('username', NEW.username)
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers to keep users and auth.users in sync
DROP TRIGGER IF EXISTS users_after_insert_trigger ON users;
CREATE TRIGGER users_after_insert_trigger
AFTER INSERT ON users
FOR EACH ROW
EXECUTE FUNCTION sync_auth_user();

-- Create JWT signing function (simplified for compatibility with Supabase)
-- Create the pgcrypto extension if not exists
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION auth.sign(payload json, secret text, algorithm text DEFAULT 'HS256')
RETURNS text LANGUAGE sql AS $$
    SELECT 
        encode(
            concat(
                encode(convert_to('{"alg":"' || algorithm || '","typ":"JWT"}', 'UTF8'), 'base64'),
                '.',
                encode(convert_to(payload::text, 'UTF8'), 'base64'),
                '.',
                encode(
                    digest(
                        encode(convert_to(payload::text, 'UTF8'), 'base64') || secret,
                        'sha256'
                    ),
                    'base64'
                )
            )::bytea,
            'base64'
        );
$$;

-- Create auth.uid() function for RLS policies
CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid AS $$
  SELECT NULLIF(current_setting('request.jwt.claims', true)::json->>'sub', '')::uuid;
$$ LANGUAGE sql STABLE;