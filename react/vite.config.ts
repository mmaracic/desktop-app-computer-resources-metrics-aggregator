import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      // Forward API calls to the FastAPI backend when running `npm run dev` standalone.
      "/api": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true,
      },
      "/websocket": {
        target: "ws://127.0.0.1:5000",
        ws: true,
      },
    },
  },
})
