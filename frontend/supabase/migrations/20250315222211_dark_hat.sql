/*
  # Fix Profiles Table RLS Policies

  1. Changes
    - Add INSERT policy for profiles table
    - Allow authenticated users to create their own profile
    - Maintain data isolation between users
*/

-- Add INSERT policy for profiles table
DO $$ BEGIN
  CREATE POLICY "Users can insert own profile"
    ON public.profiles
    FOR INSERT
    TO authenticated
    WITH CHECK (id = auth.uid());
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

-- Add UPDATE policy for profiles table with WITH CHECK clause
DO $$ BEGIN
  DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
  
  CREATE POLICY "Users can update own profile"
    ON public.profiles
    FOR UPDATE
    TO authenticated
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

-- Ensure RLS is enabled
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;