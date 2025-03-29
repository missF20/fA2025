/*
  # Assign Admin Role to User

  1. Changes
    - Find user by email
    - Assign admin role using existing function
    - Handle error cases

  2. Security
    - Uses existing secure function
    - Validates user existence
*/

DO $$
DECLARE
  target_user_id uuid;
BEGIN
  -- Get user ID from auth.users table
  SELECT id INTO target_user_id
  FROM auth.users
  WHERE email = 'hartfordtech2020@gmail.com';

  -- Check if user exists
  IF target_user_id IS NULL THEN
    RAISE EXCEPTION 'User with email hartfordtech2020@gmail.com not found';
  END IF;

  -- Assign admin role using existing function
  PERFORM assign_admin_role(target_user_id);
END;
$$;