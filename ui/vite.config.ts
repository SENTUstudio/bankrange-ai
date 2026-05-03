import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [sveltekit()],
  test: {
    environment: "jsdom",
    include: ["src/tests/unit/**/*.{test,spec}.{js,ts}"],
    globals: true,
  },
});
