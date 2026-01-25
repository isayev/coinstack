import tailwindcssAnimate from "tailwindcss-animate";

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        
        // --- Numismatic Design Tokens ---
        metal: {
          gold: "#FFD700",
          electrum: "#E8D882",
          silver: "#C0C0C0",
          orichalcum: "#C9A227",
          bronze: "#CD7F32",
          copper: "#B87333",
          ae: "#8B7355",
          billon: "#9A9A8E",
          potin: "#5C5C52",
          lead: "#6B6B7A",
        },
        grade: {
          poor: "#5AC8FA",
          good: "#64D2FF",
          fine: "#30D158",
          ef: "#FFD60A",
          au: "#FF9F0A",
          ms: "#FF6B6B",
        },
        category: {
          republic: "#C0392B",
          imperial: "#9B59B6",
          provincial: "#3498DB",
          greek: "#7D8C4E",
          byzantine: "#922B21",
        },
        rarity: {
          c: "#8E8E93",
          s: "#AF52DE",
          r1: "#5E5CE6",
          r2: "#30D158",
          r3: "#FF375F",
          u: "#FFFFFF",
        }
      },
    },
  },
  plugins: [tailwindcssAnimate],
}