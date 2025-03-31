/*
  # Fix Admin Users Policy

  1. Changes
    - Remove recursive policy
    - Add proper admin access policies
    - Add function to check admin status
    - Add proper indexes

  2. Security
    - Maintain data isolation
    - Ensure proper access control
*/

-- Drop existing admin policy to avoid conflicts
DROP POLICY IF EXISTS "Admin access" ON admin_users;

-- Create function to check if user is admin
CREATE OR REPLACE FUNCTION is_admin(user_id uuid)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 
    FROM admin_users 
    WHERE admin_users.user_id = $1
  );
END;
$$;

-- Create separate policies for different operations
CREATE POLICY "Admins can view all admin users"
  ON admin_users
  FOR SELECT
  TO authenticated
  USING (is_admin(auth.uid()));

CREATE POLICY "Admins can insert new admin users"
  ON admin_users
  FOR INSERT
  TO authenticated
  WITH CHECK (is_admin(auth.uid()));

CREATE POLICY "Admins can update admin users"
  ON admin_users
  FOR UPDATE
  TO authenticated
  USING (is_admin(auth.uid()))
  WITH CHECK (is_admin(auth.uid()));

CREATE POLICY "Admins can delete admin users"
  ON admin_users
  FOR DELETE
  TO authenticated
  USING (is_admin(auth.uid()));

-- Add index for better performance if it doesn't exist
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE tablename = 'admin_users' AND indexname = 'idx_admin_users_user_id'
  ) THEN
    CREATE INDEX idx_admin_users_user_id ON admin_users(user_id);
  END IF;
END $$;