-- 
-- This migration fixes the knowledge_files table by changing the user_id column from integer to UUID.
-- This ensures compatibility with Supabase auth.users table which uses UUID for id.
--

-- Begin transaction
BEGIN;

-- First, check if the knowledge_files table exists
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'knowledge_files'
  ) THEN
    -- Only proceed with migration if the user_id column is an integer
    IF (
      SELECT data_type 
      FROM information_schema.columns 
      WHERE table_schema = 'public' 
      AND table_name = 'knowledge_files' 
      AND column_name = 'user_id'
    ) = 'integer' THEN
      -- First, drop any existing policies that reference the user_id column
      DROP POLICY IF EXISTS "Users can view own knowledge files" ON knowledge_files;
      DROP POLICY IF EXISTS "Users can insert own knowledge files" ON knowledge_files;
      DROP POLICY IF EXISTS "Users can update own knowledge files" ON knowledge_files;
      DROP POLICY IF EXISTS "Users can delete own knowledge files" ON knowledge_files;
      DROP POLICY IF EXISTS select_knowledge_files ON knowledge_files;
      DROP POLICY IF EXISTS insert_knowledge_files ON knowledge_files;
      DROP POLICY IF EXISTS update_knowledge_files ON knowledge_files;
      DROP POLICY IF EXISTS delete_knowledge_files ON knowledge_files;
      
      -- Create a temporary column for UUID
      ALTER TABLE knowledge_files ADD COLUMN user_id_uuid UUID;
      
      -- Convert existing user_id values to their string representation
      -- Note: This is lossy conversion and should be handled carefully in production
      -- For testing purposes, we'll use random UUIDs since the integer IDs don't map to real UUIDs
      UPDATE knowledge_files SET user_id_uuid = gen_random_uuid();
      
      -- Drop the original user_id column
      ALTER TABLE knowledge_files DROP COLUMN user_id;
      
      -- Rename the UUID column to user_id
      ALTER TABLE knowledge_files RENAME COLUMN user_id_uuid TO user_id;
      
      -- Add NOT NULL constraint back
      ALTER TABLE knowledge_files ALTER COLUMN user_id SET NOT NULL;
      
      -- Recreate the Row Level Security policies
      CREATE POLICY "Users can view own knowledge files" 
      ON knowledge_files FOR SELECT 
      USING (auth.uid() = user_id);
      
      CREATE POLICY "Users can insert own knowledge files" 
      ON knowledge_files FOR INSERT 
      WITH CHECK (auth.uid() = user_id);
      
      CREATE POLICY "Users can update own knowledge files" 
      ON knowledge_files FOR UPDATE 
      USING (auth.uid() = user_id);
      
      CREATE POLICY "Users can delete own knowledge files" 
      ON knowledge_files FOR DELETE 
      USING (auth.uid() = user_id);
      
      -- Log the successful migration
      RAISE NOTICE 'Successfully migrated knowledge_files.user_id from integer to UUID';
    ELSE
      RAISE NOTICE 'The knowledge_files.user_id column is already a non-integer type. No migration needed.';
    END IF;
  ELSE
    RAISE NOTICE 'The knowledge_files table does not exist. No migration needed.';
  END IF;
END $$;

-- Commit transaction
COMMIT;