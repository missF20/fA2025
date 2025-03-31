/*
  # Fix Profile Email Population

  1. Changes
    - Update handle_new_user function to properly set email
    - Add error handling for missing email
    - Ensure proper type casting
*/

-- Update the handle_new_user function to properly handle email
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF NEW.email IS NULL THEN
    RAISE EXCEPTION 'Email is required';
  END IF;

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
    COALESCE(NEW.raw_user_meta_data->>'company', ''),
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

-- Drop and recreate the trigger to ensure it's using the latest version
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();