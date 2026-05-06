import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [sveltekit()],
  resolve: {
    conditions: ["browser"],
  },
  test: {
    environment: "jsdom",
    include: ["src/tests/unit/**/*.{test,spec}.{js,ts}"],
    globals: true,
    setupFiles: ["src/tests/unit/setup.ts"],
  },
} as any);
