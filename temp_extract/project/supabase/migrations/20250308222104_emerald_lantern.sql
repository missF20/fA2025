/*
  # Add Email Column to Profiles

  1. Changes
    - Add email column to profiles table
    - Add unique constraint on email
    - Add index for email lookups
    - Update existing profiles with email from auth.users

  2. Security
    - Maintain existing RLS policies
*/

-- Add email column if it doesn't exist
DO $$ BEGIN
  ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS email text;
EXCEPTION
  WHEN duplicate_column THEN NULL;
END $$;

-- Create index for email lookups
DO $$ BEGIN
  CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);
EXCEPTION
  WHEN duplicate_table THEN NULL;
END $$;

-- Update existing profiles with email from auth.users
DO $$ 
BEGIN
  UPDATE profiles p
  SET email = u.email
  FROM auth.users u
  WHERE p.id = u.id
  AND p.email IS NULL;
END $$;

-- Add NOT NULL constraint after populating data
DO $$ BEGIN
  ALTER TABLE profiles
  ALTER COLUMN email SET NOT NULL;
EXCEPTION
  WHEN others THEN NULL;
END $$;

-- Add unique constraint
DO $$ BEGIN
  ALTER TABLE profiles
  ADD CONSTRAINT profiles_email_unique UNIQUE (email);
EXCEPTION
  WHEN duplicate_table THEN NULL;
END $$;