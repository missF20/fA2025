/*
  # Fix Admin Policies

  1. Changes
    - Drop existing policies that cause recursion
    - Create simplified policies with direct checks
    - Add basic view policy for all authenticated users
    - Add admin management policies

  2. Security
    - Maintain proper access control
    - Prevent infinite recursion
    - Allow basic user access to own record
*/

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own admin record" ON admin_users;
DROP POLICY IF EXISTS "Admins can view all records" ON admin_users;
DROP POLICY IF EXISTS "Admins can manage records" ON admin_users;

-- Create basic view policy for authenticated users
CREATE POLICY "View own admin record"
  ON admin_users
  FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

-- Create admin management policies
CREATE POLICY "Admin select all"
  ON admin_users
  FOR SELECT
  TO authenticated
  USING (
    role = 'admin' AND user_id = auth.uid()
  );

CREATE POLICY "Admin insert"
  ON admin_users
  FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM admin_users
      WHERE user_id = auth.uid()
      AND role = 'admin'
    )
  );

CREATE POLICY "Admin update"
  ON admin_users
  FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM admin_users
      WHERE user_id = auth.uid()
      AND role = 'admin'
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM admin_users
      WHERE user_id = auth.uid()
      AND role = 'admin'
    )
  );

CREATE POLICY "Admin delete"
  ON admin_users
  FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM admin_users
      WHERE user_id = auth.uid()
      AND role = 'admin'
    )
  );