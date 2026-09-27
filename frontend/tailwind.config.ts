import type { Config } from "tailwindcss";

// Design tokens for the marketing/auth shell around the existing dashboard.
// The dashboard (workspace.tsx and its children) already uses plain Tailwind
// slate utilities directly and isn't reskinned here — these tokens extend
// the palette for the landing page, nav, and login screen so they read as
// one product rather than a bolted-on marketing site.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#FFFFFF",
        ledger: {
          50: "#EAF3EF",
          100: "#D3E7DD",
          400: "#2F7A5F",
          600: "#1F5E4A",
          700: "#194C3C",
        },
      },
      fontFamily: {
        serif: ["ui-serif", "Georgia", "Cambria", "Times New Roman", "serif"],
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      maxWidth: {
        prose: "68ch",
      },
    },
  },
  plugins: [],
};

export default config;
