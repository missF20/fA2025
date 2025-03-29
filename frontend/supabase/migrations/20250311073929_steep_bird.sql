/*
  # Fix User Creation and Profile Handling

  1. New Tables
    - Ensure profiles table has all required fields
    - Add proper constraints and defaults
    - Add subscription handling

  2. Security
    - Enable RLS
    - Add policies for user data access
    - Ensure proper data isolation

  3. Changes
    - Update trigger function for user creation
    - Add cascading deletes
    - Fix email handling
*/

-- Ensure profiles table has all required fields
CREATE TABLE IF NOT EXISTS public.profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email text NOT NULL,
  company text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  account_setup_complete boolean DEFAULT false,
  welcome_email_sent boolean DEFAULT false,
  subscription_tier_id uuid REFERENCES public.subscription_tiers(id),
  onboarding_completed boolean DEFAULT false
);

-- Add unique constraint on email
ALTER TABLE public.profiles
  DROP CONSTRAINT IF EXISTS profiles_email_unique,
  ADD CONSTRAINT profiles_email_unique UNIQUE (email);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);

-- Create or replace the handle_new_user function
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (
    id,
    email,
    company,
    account_setup_complete,
    welcome_email_sent,
    onboarding_completed,
    created_at,
    updated_at
  )
  VALUES (
    NEW.id,
    NEW.email,
    NEW.raw_user_meta_data->>'company',
    false,
    false,
    false,
    NOW(),
    NOW()
  )
  ON CONFLICT (id) DO UPDATE
  SET
    email = EXCLUDED.email,
    company = EXCLUDED.company,
    updated_at = NOW();

  RETURN NEW;
END;
$$;

-- Drop and recreate the trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Enable RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Create policies
DO $$
BEGIN
  -- Users can read their own profile
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE tablename = 'profiles' AND policyname = 'Users can view own profile'
  ) THEN
    CREATE POLICY "Users can view own profile"
      ON public.profiles
      FOR SELECT
      TO authenticated
      USING (id = auth.uid());
  END IF;

  -- Users can update their own profile
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE tablename = 'profiles' AND policyname = 'Users can update own profile'
  ) THEN
    CREATE POLICY "Users can update own profile"
      ON public.profiles
      FOR UPDATE
      TO authenticated
      USING (id = auth.uid())
      WITH CHECK (id = auth.uid());
  END IF;
END $$;

-- Add cascading deletes for all user-related tables
DO $$
BEGIN
  -- Update conversations foreign key
  ALTER TABLE public.conversations
    DROP CONSTRAINT IF EXISTS conversations_user_id_fkey,
    ADD CONSTRAINT conversations_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES auth.users(id)
    ON DELETE CASCADE;

  -- Update interactions foreign key
  ALTER TABLE public.interactions
    DROP CONSTRAINT IF EXISTS interactions_user_id_fkey,
    ADD CONSTRAINT interactions_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES auth.users(id)
    ON DELETE CASCADE;

  -- Update knowledge_files foreign key
  ALTER TABLE public.knowledge_files
    DROP CONSTRAINT IF EXISTS knowledge_files_user_id_fkey,
    ADD CONSTRAINT knowledge_files_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES auth.users(id)
    ON DELETE CASCADE;

  -- Update responses foreign key
  ALTER TABLE public.responses
    DROP CONSTRAINT IF EXISTS responses_user_id_fkey,
    ADD CONSTRAINT responses_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES auth.users(id)
    ON DELETE CASCADE;

  -- Update tasks foreign key
  ALTER TABLE public.tasks
    DROP CONSTRAINT IF EXISTS tasks_user_id_fkey,
    ADD CONSTRAINT tasks_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES auth.users(id)
    ON DELETE CASCADE;

  -- Update user_subscriptions foreign key
  ALTER TABLE public.user_subscriptions
    DROP CONSTRAINT IF EXISTS user_subscriptions_user_id_fkey,
    ADD CONSTRAINT user_subscriptions_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES auth.users(id)
    ON DELETE CASCADE;
END $$;