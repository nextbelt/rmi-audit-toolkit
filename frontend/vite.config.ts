import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
    // Polling fallback for OneDrive / network folders where native fs watching is unreliable
    watch: {
      usePolling: true,
      interval: 400,
    },
  },
  preview: {
    allowedHosts: [
      'rmi-audit-toolkit-frontend-production.up.railway.app',
      '.railway.app',
    ],
  },
});
