import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Builds into Django's static/ tree with fixed filenames (no hash) — a Django
// template just references /static/spa/main.js directly, no manifest parsing needed.
export default defineConfig({
  plugins: [react()],
  base: "/static/spa/",
  server: {
    proxy: {
      "/api": "http://localhost:8000",
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
  build: {
    outDir: "../qless_cafe/static/spa",
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: "main.js",
        chunkFileNames: "[name].js",
        assetFileNames: "main.[ext]",
      },
    },
  },
});
