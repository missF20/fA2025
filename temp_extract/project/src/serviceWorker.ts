import { Workbox } from 'workbox-window';
import { log } from './utils/logger';

export function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    const wb = new Workbox('/sw.js');

    wb.addEventListener('installed', (event) => {
      if (event.isUpdate) {
        if (confirm('New version available! Reload to update?')) {
          window.location.reload();
        }
      }
    });

    wb.addEventListener('activated', () => {
      log.info('Service Worker activated');
    });

    wb.addEventListener('waiting', () => {
      log.info('Service Worker waiting');
    });

    wb.register().catch((error) => {
      log.error('Service Worker registration failed:', error);
    });
  }
}