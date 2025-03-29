/*
  # Fix Admin Role Assignment Function

  1. Changes
    - Drop existing function
    - Recreate with correct parameter name
    - Add proper security checks

  2. Security
    - Maintain SECURITY DEFINER
    - Add proper parameter validation
*/

-- Drop existing function
DROP FUNCTION IF EXISTS assign_admin_role(uuid);

-- Create function to assign admin role with proper parameter name
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

  -- Insert or update admin role
  INSERT INTO admin_users (user_id, role)
  VALUES (target_user_id, 'admin')
  ON CONFLICT (user_id) 
  DO UPDATE SET 
    role = 'admin',
    updated_at = now();
END;
$$;