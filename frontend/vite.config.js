import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
//
// Two backend proxies:
//   /api/*    → FastAPI on :3002
//   /static/* → FastAPI on :3002  (so the React dev server can play
//                                  videos served by the Python backend)
//
// The frontend uses absolute URLs (http://localhost:3002/...) by
// default — this proxy is just a convenience for browser CORS-free
// access. Override with VITE_API_BASE if you deploy them separately.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: false,
    proxy: {
      '/api': 'http://localhost:3002',
      '/static': 'http://localhost:3002',
    },
  },
})