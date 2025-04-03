-- Add binary_data column to knowledge_files table

-- Check if binary_data column exists, if not, add it
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'knowledge_files' AND column_name = 'binary_data'
    ) THEN
        ALTER TABLE knowledge_files ADD COLUMN binary_data TEXT;
    END IF;
END
$$;

-- Refresh Supabase schema cache
NOTIFY pgrst, 'reload schema';