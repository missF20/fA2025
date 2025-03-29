/*
  # Fix Admin User Authentication and Policies

  1. Changes
    - Create admin user with proper authentication
    - Add unique constraint on admin_users.user_id
    - Update admin policies
    - Fix profile creation

  2. Security
    - Ensure proper password hashing
    - Add proper constraints
*/

-- Add unique constraint to admin_users.user_id
ALTER TABLE public.admin_users 
  DROP CONSTRAINT IF EXISTS admin_users_user_id_key,
  ADD CONSTRAINT admin_users_user_id_key UNIQUE (user_id);

-- Drop existing admin policies
DROP POLICY IF EXISTS "Admins can view all admin users" ON admin_users;
DROP POLICY IF EXISTS "Admins can insert new admin users" ON admin_users;
DROP POLICY IF EXISTS "Admins can update admin users" ON admin_users;
DROP POLICY IF EXISTS "Admins can delete admin users" ON admin_users;

-- Create admin user
DO $$
DECLARE
  admin_user_id uuid := '00000000-0000-0000-0000-000000000001';
  admin_email text := 'admin@hartford-tech.com';
BEGIN
  -- Create admin user if not exists
  INSERT INTO auth.users (
    id,
    instance_id,
    email,
    encrypted_password,
    email_confirmed_at,
    created_at,
    updated_at,
    raw_app_meta_data,
    raw_user_meta_data,
    is_super_admin,
    role,
    confirmation_token,
    recovery_token
  )
  VALUES (
    admin_user_id,
    '00000000-0000-0000-0000-000000000000',
    admin_email,
    crypt('ht20ht20', gen_salt('bf')),
    now(),
    now(),
    now(),
    '{"provider":"email","providers":["email"]}',
    '{"role":"admin"}',
    false,
    'authenticated',
    encode(gen_random_bytes(32), 'hex'),
    encode(gen_random_bytes(32), 'hex')
  )
  ON CONFLICT (id) DO UPDATE
  SET 
    email = EXCLUDED.email,
    encrypted_password = EXCLUDED.encrypted_password,
    updated_at = now();

  -- Ensure profile exists
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
    admin_user_id,
    admin_email,
    'Hartford Tech',
    true,
    true,
    true,
    now(),
    now()
  )
  ON CONFLICT (id) DO UPDATE
  SET 
    email = EXCLUDED.email,
    company = EXCLUDED.company,
    updated_at = now();

  -- Create admin role
  INSERT INTO public.admin_users (
    id,
    user_id,
    role,
    created_at,
    updated_at
  )
  VALUES (
    gen_random_uuid(),
    admin_user_id,
    'admin',
    now(),
    now()
  )
  ON CONFLICT ON CONSTRAINT admin_users_user_id_key 
  DO UPDATE SET
    role = EXCLUDED.role,
    updated_at = now();

END $$;

-- Create new admin policies
CREATE POLICY "Admins can view all admin users"
  ON admin_users
  FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM admin_users WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Admins can insert new admin users"
  ON admin_users
  FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM admin_users WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Admins can update admin users"
  ON admin_users
  FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM admin_users WHERE user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM admin_users WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Admins can delete admin users"
  ON admin_users
  FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM admin_users WHERE user_id = auth.uid()
    )
  );