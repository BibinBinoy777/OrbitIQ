import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": process.env.ORBITIQ_BACKEND_URL ?? "http://127.0.0.1:8000",
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test-setup.ts"],
    // Read the standalone export stylesheet; jsdom cannot parse paged margin boxes.
    // Actual preview/print layout is verified in supported browsers.
    css: { include: [/\?raw$/] },
  },
});
