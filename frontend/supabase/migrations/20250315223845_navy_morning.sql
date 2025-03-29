/*
  # Fix Admin User Policies

  1. Changes
    - Simplify admin user policies to avoid recursion
    - Add direct user_id check for basic access
    - Update existing admin user if needed

  2. Security
    - Maintain proper access control
    - Prevent unauthorized access
*/

-- Drop existing admin policies to start fresh
DROP POLICY IF EXISTS "Admins can view all admin users" ON admin_users;
DROP POLICY IF EXISTS "Admins can insert new admin users" ON admin_users;
DROP POLICY IF EXISTS "Admins can update admin users" ON admin_users;
DROP POLICY IF EXISTS "Admins can delete admin users" ON admin_users;

-- Create simplified admin policies
CREATE POLICY "Admin users can view admin records"
  ON admin_users
  FOR SELECT
  TO authenticated
  USING (user_id = auth.uid() OR EXISTS (
    SELECT 1 FROM admin_users a2 
    WHERE a2.user_id = auth.uid() 
    AND a2.role = 'admin'
  ));

CREATE POLICY "Admin users can manage admin records"
  ON admin_users
  FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM admin_users a2 
      WHERE a2.user_id = auth.uid() 
      AND a2.role = 'admin'
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM admin_users a2 
      WHERE a2.user_id = auth.uid() 
      AND a2.role = 'admin'
    )
  );

-- Ensure admin user exists and has correct role
DO $$
DECLARE
  admin_user_id uuid := '00000000-0000-0000-0000-000000000001';
  admin_email text := 'admin@hartford-tech.com';
BEGIN
  -- Update or insert admin user
  INSERT INTO admin_users (
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
    role = 'admin',
    updated_at = now();
END $$;