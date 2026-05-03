/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{html,js,svelte,ts}"],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', "monospace"],
      },
      colors: {
        tactical: {
          bg: "#0a0a0a",
          panel: "#111111",
          border: "#222222",
          text: "#e0e0e0",
          muted: "#888888",
          alert: "#ff3333",
          warn: "#ffaa00",
          success: "#33ff33",
          primary: "#00ccff",
        },
      },
    },
  },
  plugins: [],
};
