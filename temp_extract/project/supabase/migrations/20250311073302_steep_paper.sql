/*
  # Fix User Creation and Profile Handling

  1. Changes
    - Add proper constraints and defaults for profiles table
    - Update profile creation trigger
    - Fix email handling
    - Add proper cascading for user deletion

  2. Security
    - Maintain existing RLS policies
    - Ensure proper user isolation
*/

-- Update profiles table constraints and defaults
DO $$
BEGIN
  -- Add email column if it doesn't exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'profiles' AND column_name = 'email'
  ) THEN
    ALTER TABLE public.profiles ADD COLUMN email text;
  END IF;

  -- Add subscription_tier_id if it doesn't exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'profiles' AND column_name = 'subscription_tier_id'
  ) THEN
    ALTER TABLE public.profiles ADD COLUMN subscription_tier_id uuid REFERENCES subscription_tiers(id);
  END IF;

  -- Set default values for boolean fields
  ALTER TABLE public.profiles 
    ALTER COLUMN account_setup_complete SET DEFAULT false,
    ALTER COLUMN welcome_email_sent SET DEFAULT false,
    ALTER COLUMN onboarding_completed SET DEFAULT false;

  -- Add unique constraint on email if it doesn't exist
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'profiles_email_unique'
  ) THEN
    ALTER TABLE public.profiles ADD CONSTRAINT profiles_email_unique UNIQUE (email);
  END IF;
END $$;

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

-- Update RLS policies for profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

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

-- Add cascading deletes for user-related data
DO $$
BEGIN
  -- Update foreign key constraints with CASCADE
  ALTER TABLE public.conversations
    DROP CONSTRAINT IF EXISTS conversations_user_id_fkey,
    ADD CONSTRAINT conversations_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES auth.users(id)
    ON DELETE CASCADE;

  ALTER TABLE public.interactions
    DROP CONSTRAINT IF EXISTS interactions_user_id_fkey,
    ADD CONSTRAINT interactions_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES auth.users(id)
    ON DELETE CASCADE;

  ALTER TABLE public.knowledge_files
    DROP CONSTRAINT IF EXISTS knowledge_files_user_id_fkey,
    ADD CONSTRAINT knowledge_files_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES auth.users(id)
    ON DELETE CASCADE;

  ALTER TABLE public.responses
    DROP CONSTRAINT IF EXISTS responses_user_id_fkey,
    ADD CONSTRAINT responses_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES auth.users(id)
    ON DELETE CASCADE;

  ALTER TABLE public.tasks
    DROP CONSTRAINT IF EXISTS tasks_user_id_fkey,
    ADD CONSTRAINT tasks_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES auth.users(id)
    ON DELETE CASCADE;

  ALTER TABLE public.user_subscriptions
    DROP CONSTRAINT IF EXISTS user_subscriptions_user_id_fkey,
    ADD CONSTRAINT user_subscriptions_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES auth.users(id)
    ON DELETE CASCADE;
END $$;