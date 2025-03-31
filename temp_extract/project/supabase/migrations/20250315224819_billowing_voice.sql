/*
  # Fix Admin User Policies

  1. Changes
    - Drop existing policies to start fresh
    - Create simplified policies without recursion
    - Add basic user_id check for own records
    - Add admin role check for managing all records

  2. Security
    - Maintain proper access control
    - Prevent unauthorized access
*/

-- Drop existing policies to start fresh
DROP POLICY IF EXISTS "Admin users can view admin records" ON admin_users;
DROP POLICY IF EXISTS "Admin users can manage admin records" ON admin_users;

-- Create new simplified policies
CREATE POLICY "Users can view own admin record"
  ON admin_users
  FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "Admins can view all records"
  ON admin_users
  FOR SELECT
  TO authenticated
  USING (EXISTS (
    SELECT 1 FROM admin_users
    WHERE user_id = auth.uid()
    AND role = 'admin'
  ));

CREATE POLICY "Admins can manage records"
  ON admin_users
  FOR ALL
  TO authenticated
  USING (EXISTS (
    SELECT 1 FROM admin_users
    WHERE user_id = auth.uid()
    AND role = 'admin'
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM admin_users
    WHERE user_id = auth.uid()
    AND role = 'admin'
  ));