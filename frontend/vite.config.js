/**
 * ============================================
 * VITE CONFIGURATION
 * ============================================
 * 
 * Vite is a fast build tool for modern web apps.
 * It replaces Webpack with much faster builds.
 * 
 * Docs: https://vitejs.dev/
 */

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: true, // Auto-open browser when starting dev server
  },
});

