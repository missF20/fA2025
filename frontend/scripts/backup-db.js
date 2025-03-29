import { createClient } from '@supabase/supabase-js';
import fs from 'fs/promises';
import path from 'path';

const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_SERVICE_ROLE_KEY
);

async function backupDatabase() {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const backupDir = path.join(process.cwd(), 'backups');
  
  try {
    // Create backups directory if it doesn't exist
    await fs.mkdir(backupDir, { recursive: true });

    // Tables to backup
    const tables = [
      'profiles',
      'subscription_tiers',
      'user_subscriptions',
      'conversations',
      'messages',
      'responses',
      'tasks',
      'interactions',
      'knowledge_files',
      'admin_users'
    ];

    // Backup each table
    for (const table of tables) {
      const { data, error } = await supabase
        .from(table)
        .select('*');

      if (error) throw error;

      const filePath = path.join(backupDir, `${table}_${timestamp}.json`);
      await fs.writeFile(filePath, JSON.stringify(data, null, 2));
      console.log(`Backed up ${table} to ${filePath}`);
    }

    console.log('Database backup completed successfully');
  } catch (error) {
    console.error('Error backing up database:', error);
    process.exit(1);
  }
}

backupDatabase();