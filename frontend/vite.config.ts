import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // stub native canvas during tests / node env to avoid canvas.node import errors
      canvas: path.resolve(__dirname, 'src/test-utils/canvas-stub.ts'),
    },
  },
  server: {
    port: 5173,
    open: true,
  },
});
