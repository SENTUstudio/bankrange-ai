/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{html,js,svelte,ts}"],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', "monospace"],
      },
      colors: {
        panel: {
          bg: "var(--bg-primary)",
          sidebar: "rgb(var(--bg-panel-rgb) / <alpha-value>)",
          hover: "var(--bg-panel-hover)",
        },
        border: {
          DEFAULT: "var(--border-color)",
          glow: "var(--border-glow)",
        },
        brand: {
          cyan: "rgb(var(--cyan-rgb) / <alpha-value>)",
          "cyan-10": "var(--cyan-10)",
          "cyan-20": "var(--cyan-20)",
          "cyan-dim": "var(--cyan-dim)",
          red: "rgb(var(--alert-red-rgb) / <alpha-value>)",
          orange: "rgb(var(--alert-orange-rgb) / <alpha-value>)",
          green: "rgb(var(--alert-green-rgb) / <alpha-value>)",
        },
        content: {
          primary: "var(--text-primary)",
          secondary: "var(--text-secondary)",
          dim: "var(--text-dim)",
        },
        // Legacy tactical palette (hardcoded for backward compat)
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
      width: {
        sidebar: "var(--sidebar-width)",
      },
      spacing: {
        "status-bar": "var(--status-bar-height)",
      },
    },
  },
  plugins: [],
};
