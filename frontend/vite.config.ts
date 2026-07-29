import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Port 8000 is often taken by other local apps; scaffold defaults to 8001.
const apiTarget = process.env.VITE_API_TARGET ?? "http://127.0.0.1:8001";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: apiTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
