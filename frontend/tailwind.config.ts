import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "rgba(255,255,255,0.12)",
        surface: "rgba(15,23,42,0.62)",
        ink: "#e2e8f0",
      },
      boxShadow: {
        glass: "0 18px 70px rgba(2, 6, 23, 0.34)",
        glow: "0 0 0 1px rgba(34, 211, 238, 0.16), 0 16px 48px rgba(8, 145, 178, 0.16)",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
} satisfies Config;
