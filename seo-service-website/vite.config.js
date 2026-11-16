import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    // `npm run dev` talks to the Flask backend started with `python -m src.main` (port 5000).
    proxy: {
      '/api': process.env.VITE_API_TARGET || 'http://127.0.0.1:5000',
    },
  },
})
