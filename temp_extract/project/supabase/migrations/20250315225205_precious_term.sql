/*
  # Create Admin User System

  1. Changes
    - Add unique constraint to admin_users.user_id
    - Create simple policies for admin access
    - Add function to assign admin role

  2. Security
    - Ensure proper access control
    - Prevent unauthorized admin assignments
*/

-- Add unique constraint to admin_users.user_id if it doesn't exist
ALTER TABLE public.admin_users 
  DROP CONSTRAINT IF EXISTS admin_users_user_id_key,
  ADD CONSTRAINT admin_users_user_id_key UNIQUE (user_id);

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own admin record" ON admin_users;
DROP POLICY IF EXISTS "Admins can view all records" ON admin_users;
DROP POLICY IF EXISTS "Admins can manage records" ON admin_users;

-- Create simple policies
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

-- Create function to assign admin role
CREATE OR REPLACE FUNCTION assign_admin_role(user_id uuid)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  INSERT INTO admin_users (user_id, role)
  VALUES ($1, 'admin')
  ON CONFLICT (user_id) 
  DO UPDATE SET role = 'admin', updated_at = now();
END;
$$;