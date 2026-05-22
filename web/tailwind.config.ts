import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        wc: {
          50:  "#fef3f2",
          100: "#fee4e2",
          400: "#f97066",
          500: "#f04438",
          600: "#d92d20",
          700: "#b42318",
          800: "#912018",
          900: "#7a271a",
        },
        wcgold: {
          50: "#fffaeb",
          400: "#fdb022",
          500: "#f79009",
          600: "#dc6803",
        },
      },
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
      keyframes: {
        slideIn: { "0%": { opacity: "0", transform: "translateY(-8px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
      },
      animation: { slideIn: "slideIn 0.35s ease-out" },
    },
  },
  plugins: [],
} satisfies Config;
