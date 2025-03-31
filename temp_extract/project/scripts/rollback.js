import fs from 'fs/promises';
import path from 'path';

async function rollback() {
  try {
    const backupDir = path.join(process.cwd(), 'backups');
    const deployDir = path.join(process.cwd(), 'dist');
    const rollbackDir = path.join(process.cwd(), 'rollbacks');

    // Get latest backup
    const backups = await fs.readdir(backupDir);
    const latestBackup = backups
      .filter(f => f.endsWith('.tar.gz'))
      .sort()
      .reverse()[0];

    if (!latestBackup) {
      throw new Error('No backup found');
    }

    // Create rollbacks directory if it doesn't exist
    await fs.mkdir(rollbackDir, { recursive: true });

    // Backup current deployment
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const currentBackup = path.join(rollbackDir, `deploy-${timestamp}.tar.gz`);
    
    await fs.copyFile(
      path.join(deployDir, 'deploy.tar.gz'),
      currentBackup
    );

    // Restore from backup
    await fs.copyFile(
      path.join(backupDir, latestBackup),
      path.join(deployDir, 'deploy.tar.gz')
    );

    console.log('Rollback completed successfully');
  } catch (error) {
    console.error('Rollback failed:', error);
    process.exit(1);
  }
}

rollback();