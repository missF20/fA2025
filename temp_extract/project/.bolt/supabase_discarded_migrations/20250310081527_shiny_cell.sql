/*
  # Fix Authentication and User Setup

  1. User Setup
    - Create auth schema extensions if not exists
    - Set up initial users with proper roles
    - Create necessary profiles and subscriptions

  2. Security
    - Enable RLS
    - Add proper policies
*/

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table if it doesn't exist
CREATE TABLE IF NOT EXISTS auth.users (
  id uuid PRIMARY KEY,
  email text UNIQUE,
  encrypted_password text,
  created_at timestamptz DEFAULT now()
);

-- Ensure profiles table exists with correct structure
CREATE TABLE IF NOT EXISTS public.profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id),
  email text UNIQUE NOT NULL,
  company text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  account_setup_complete boolean DEFAULT false,
  welcome_email_sent boolean DEFAULT false,
  subscription_tier_id uuid REFERENCES subscription_tiers(id),
  onboarding_completed boolean DEFAULT false
);

-- Create admin users table if not exists
CREATE TABLE IF NOT EXISTS public.admin_users (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users(id),
  role text CHECK (role IN ('admin', 'support', 'billing')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admin_users ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view own profile"
  ON public.profiles
  FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.profiles
  FOR UPDATE
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Admin users can view admin data"
  ON public.admin_users
  FOR SELECT
  TO authenticated
  USING (EXISTS (
    SELECT 1 FROM admin_users WHERE user_id = auth.uid()
  ));

-- Insert test users
DO $$
DECLARE
  regular_user_id uuid;
  admin_user_id uuid;
  enterprise_tier_id uuid;
BEGIN
  -- Get or create enterprise tier
  INSERT INTO subscription_tiers (
    id, 
    name, 
    description, 
    price, 
    features,
    platforms
  )
  VALUES (
    uuid_generate_v4(),
    'Enterprise',
    'Full access to all platforms and features',
    299.99,
    ARRAY['All platforms support', '24/7 priority support', 'Custom integrations'],
    ARRAY['facebook', 'instagram', 'whatsapp']
  )
  ON CONFLICT (name) DO NOTHING
  RETURNING id INTO enterprise_tier_id;

  -- Create regular user
  INSERT INTO auth.users (id, email, encrypted_password)
  VALUES (
    uuid_generate_v4(),
    'hartfordtech2020@gmail.com',
    crypt('Ht2020', gen_salt('bf'))
  )
  ON CONFLICT (email) DO NOTHING
  RETURNING id INTO regular_user_id;

  -- Create regular user profile
  INSERT INTO profiles (
    id,
    email,
    company,
    account_setup_complete,
    subscription_tier_id
  )
  VALUES (
    regular_user_id,
    'hartfordtech2020@gmail.com',
    'Hartford Tech',
    true,
    enterprise_tier_id
  )
  ON CONFLICT (id) DO NOTHING;

  -- Create admin user
  INSERT INTO auth.users (id, email, encrypted_password)
  VALUES (
    uuid_generate_v4(),
    'admin@hartfordtech.com',
    crypt('ht20ht20', gen_salt('bf'))
  )
  ON CONFLICT (email) DO NOTHING
  RETURNING id INTO admin_user_id;

  -- Create admin user profile and admin role
  INSERT INTO profiles (
    id,
    email,
    company,
    account_setup_complete
  )
  VALUES (
    admin_user_id,
    'admin@hartfordtech.com',
    'Hartford Tech Admin',
    true
  )
  ON CONFLICT (id) DO NOTHING;

  INSERT INTO admin_users (
    user_id,
    role
  )
  VALUES (
    admin_user_id,
    'admin'
  )
  ON CONFLICT (user_id) DO NOTHING;

END $$;