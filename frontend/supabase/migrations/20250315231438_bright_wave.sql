/*
  # Admin Role Management System

  1. Changes
    - Drop existing admin policies to avoid conflicts
    - Create proper admin check functions
    - Add secure policies for admin management
    - Add function to safely assign admin roles

  2. Security
    - Ensure proper authorization checks
    - Prevent policy recursion
    - Add proper parameter validation
*/

-- Drop existing policies to start fresh
DROP POLICY IF EXISTS "Users can view own admin record" ON admin_users;
DROP POLICY IF EXISTS "Admins can view all records" ON admin_users;
DROP POLICY IF EXISTS "Admins can manage records" ON admin_users;

-- Drop existing functions
DROP FUNCTION IF EXISTS assign_admin_role(uuid);
DROP FUNCTION IF EXISTS is_admin();

-- Create basic admin check function
CREATE OR REPLACE FUNCTION is_admin()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM admin_users 
    WHERE user_id = auth.uid() 
    AND role = 'admin'
  );
$$;

-- Create function to assign admin role
CREATE OR REPLACE FUNCTION assign_admin_role(target_user_id uuid)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  -- Validate target user exists
  IF NOT EXISTS (SELECT 1 FROM auth.users WHERE id = target_user_id) THEN
    RAISE EXCEPTION 'User not found';
  END IF;

  -- Check if executing user is admin
  IF NOT is_admin() THEN
    RAISE EXCEPTION 'Only administrators can assign admin roles';
  END IF;

  -- Insert or update admin role
  INSERT INTO admin_users (
    id,
    user_id,
    role,
    created_at,
    updated_at
  )
  VALUES (
    gen_random_uuid(),
    target_user_id,
    'admin',
    now(),
    now()
  )
  ON CONFLICT (user_id) 
  DO UPDATE SET 
    role = 'admin',
    updated_at = now();
END;
$$;

-- Create simplified policies
CREATE POLICY "View own admin record"
  ON admin_users
  FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "Admin view all"
  ON admin_users
  FOR SELECT
  TO authenticated
  USING (is_admin());

CREATE POLICY "Admin manage"
  ON admin_users
  FOR ALL
  TO authenticated
  USING (is_admin())
  WITH CHECK (is_admin());

-- Ensure unique constraint exists
ALTER TABLE public.admin_users 
  DROP CONSTRAINT IF EXISTS admin_users_user_id_key,
  ADD CONSTRAINT admin_users_user_id_key UNIQUE (user_id);

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_admin_users_user_id ON admin_users(user_id);

-- Enable RLS
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;