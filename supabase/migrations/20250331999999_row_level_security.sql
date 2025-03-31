-- Migration to set up Row Level Security policies for all tables
-- This requires the auth schema to already exist

-- Check if RLS is supported in this PostgreSQL version
DO $$
BEGIN
    -- Enable Row Level Security on each table
    -- Profiles table
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'profiles') THEN
        ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
        
        -- Create policies for the profiles table
        DROP POLICY IF EXISTS select_profiles ON profiles;
        CREATE POLICY select_profiles 
            ON profiles
            FOR SELECT 
            USING (id::text = auth.uid()::text);
            
        DROP POLICY IF EXISTS insert_profiles ON profiles;
        CREATE POLICY insert_profiles 
            ON profiles
            FOR INSERT 
            WITH CHECK (id::text = auth.uid()::text);
            
        DROP POLICY IF EXISTS update_profiles ON profiles;
        CREATE POLICY update_profiles 
            ON profiles
            FOR UPDATE 
            USING (id::text = auth.uid()::text);
            
        DROP POLICY IF EXISTS delete_profiles ON profiles;
        CREATE POLICY delete_profiles 
            ON profiles
            FOR DELETE 
            USING (id::text = auth.uid()::text);
    END IF;
    
    -- Conversations table
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'conversations') THEN
        ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
        
        -- Create policies for the conversations table
        DROP POLICY IF EXISTS select_conversations ON conversations;
        CREATE POLICY select_conversations 
            ON conversations
            FOR SELECT 
            USING (user_id::text = auth.uid()::text);
            
        DROP POLICY IF EXISTS insert_conversations ON conversations;
        CREATE POLICY insert_conversations 
            ON conversations
            FOR INSERT 
            WITH CHECK (user_id::text = auth.uid()::text);
            
        DROP POLICY IF EXISTS update_conversations ON conversations;
        CREATE POLICY update_conversations 
            ON conversations
            FOR UPDATE 
            USING (user_id::text = auth.uid()::text);
            
        DROP POLICY IF EXISTS delete_conversations ON conversations;
        CREATE POLICY delete_conversations 
            ON conversations
            FOR DELETE 
            USING (user_id::text = auth.uid()::text);
    END IF;
    
    -- Messages table
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'messages') THEN
        ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
        
        -- Create policies for the messages table using join with conversations
        DROP POLICY IF EXISTS select_messages ON messages;
        CREATE POLICY select_messages 
            ON messages
            FOR SELECT 
            USING (
                EXISTS (
                    SELECT 1 
                    FROM conversations 
                    WHERE conversations.id = messages.conversation_id 
                    AND conversations.user_id::text = auth.uid()::text
                )
            );
            
        DROP POLICY IF EXISTS insert_messages ON messages;
        CREATE POLICY insert_messages 
            ON messages
            FOR INSERT 
            WITH CHECK (
                EXISTS (
                    SELECT 1 
                    FROM conversations 
                    WHERE conversations.id = messages.conversation_id 
                    AND conversations.user_id::text = auth.uid()::text
                )
            );
            
        DROP POLICY IF EXISTS update_messages ON messages;
        CREATE POLICY update_messages 
            ON messages
            FOR UPDATE 
            USING (
                EXISTS (
                    SELECT 1 
                    FROM conversations 
                    WHERE conversations.id = messages.conversation_id 
                    AND conversations.user_id::text = auth.uid()::text
                )
            );
            
        DROP POLICY IF EXISTS delete_messages ON messages;
        CREATE POLICY delete_messages 
            ON messages
            FOR DELETE 
            USING (
                EXISTS (
                    SELECT 1 
                    FROM conversations 
                    WHERE conversations.id = messages.conversation_id 
                    AND conversations.user_id::text = auth.uid()::text
                )
            );
    END IF;
    
    -- Knowledge files table
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'knowledge_files') THEN
        ALTER TABLE knowledge_files ENABLE ROW LEVEL SECURITY;
        
        -- Create policies for the knowledge_files table
        DROP POLICY IF EXISTS select_knowledge_files ON knowledge_files;
        CREATE POLICY select_knowledge_files 
            ON knowledge_files
            FOR SELECT 
            USING (user_id::text = auth.uid()::text);
            
        DROP POLICY IF EXISTS insert_knowledge_files ON knowledge_files;
        CREATE POLICY insert_knowledge_files 
            ON knowledge_files
            FOR INSERT 
            WITH CHECK (user_id::text = auth.uid()::text);
            
        DROP POLICY IF EXISTS update_knowledge_files ON knowledge_files;
        CREATE POLICY update_knowledge_files 
            ON knowledge_files
            FOR UPDATE 
            USING (user_id::text = auth.uid()::text);
            
        DROP POLICY IF EXISTS delete_knowledge_files ON knowledge_files;
        CREATE POLICY delete_knowledge_files 
            ON knowledge_files
            FOR DELETE 
            USING (user_id::text = auth.uid()::text);
    END IF;
    
    -- Integration configs table
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'integration_configs') THEN
        ALTER TABLE integration_configs ENABLE ROW LEVEL SECURITY;
        
        -- Create policies for the integration_configs table
        DROP POLICY IF EXISTS select_integration_configs ON integration_configs;
        CREATE POLICY select_integration_configs 
            ON integration_configs
            FOR SELECT 
            USING (user_id::text = auth.uid()::text);
            
        DROP POLICY IF EXISTS insert_integration_configs ON integration_configs;
        CREATE POLICY insert_integration_configs 
            ON integration_configs
            FOR INSERT 
            WITH CHECK (user_id::text = auth.uid()::text);
            
        DROP POLICY IF EXISTS update_integration_configs ON integration_configs;
        CREATE POLICY update_integration_configs 
            ON integration_configs
            FOR UPDATE 
            USING (user_id::text = auth.uid()::text);
            
        DROP POLICY IF EXISTS delete_integration_configs ON integration_configs;
        CREATE POLICY delete_integration_configs 
            ON integration_configs
            FOR DELETE 
            USING (user_id::text = auth.uid()::text);
    END IF;
END
$$;