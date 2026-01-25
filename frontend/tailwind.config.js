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
      screens: {
        '3xl': '1920px',  // Full HD / Large desktop
        '4xl': '2560px',  // QHD / Ultrawide
        '5xl': '3840px',  // 4K UHD
      },
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
        
        // --- Numismatic Design Tokens V3.0 SPEC ---
        metal: {
          gold: "#FFD700",          // Au (Z=79)
          electrum: "#E8D882",      // Au+Ag natural alloy
          silver: "#C0C0C0",        // Ag (Z=47)
          orichalcum: "#C9A227",    // GOLDEN brass (Roman)
          brass: "#B5A642",         // Cu+Zn
          bronze: "#CD7F32",        // Cu+Sn
          copper: "#B87333",        // Cu (Z=29)
          ae: "#8B7355",            // Aes (generic bronze)
          billon: "#9A9A8E",        // Ag+Cu debased
          potin: "#5C5C52",         // Cu+Sn+Pb Celtic
          lead: "#6B6B7A",          // Pb (Z=82)
        },
        grade: {
          poor: "#3B82F6",          // ❄️ Freezing blue (P/FR/AG)
          good: "#64D2FF",          // 🧊 Cold teal (G/VG)
          fine: "#34C759",          // 🌡️ Neutral green (F/VF)
          ef: "#FFD60A",            // ☀️ Warm yellow (EF/XF)
          au: "#FF9F0A",            // 🔥 Hot orange (AU)
          ms: "#FF6B6B",            // 🔥 Fire red (MS/FDC)
          ngc: "#1A73E8",           // NGC brand blue
          pcgs: "#2E7D32",          // PCGS brand green
        },
        category: {
          republic: "#DC2626",      // Terracotta red (509-27 BCE)
          imperial: "#7C3AED",      // Tyrian purple (27 BCE - 284 CE)
          provincial: "#2563EB",    // Aegean blue (Greek Imperial)
          late: "#D4AF37",          // Byzantine gold (284-491 CE)
          greek: "#16A34A",         // Olive (pre-Roman)
          celtic: "#27AE60",        // Forest green (Northern Europe)
          judaea: "#C2956E",        // Desert sand/stone
          eastern: "#17A589",       // Persian turquoise (Parthian/Sasanian)
          byzantine: "#922B21",     // Imperial crimson (491+ CE)
          other: "#6e6e73",         // Neutral gray
        },
        rarity: {
          c: "#D1D5DB",             // Quartz (Common)
          s: "#8B5CF6",             // Amethyst (Scarce)
          r1: "#06B6D4",            // Sapphire - CYAN! (Rare)
          r2: "#10B981",            // Emerald (Very Rare)
          r3: "#EF4444",            // Ruby (Extremely Rare)
          u: "#FFFFFF",             // Diamond (Unique)
        },
        performance: {
          positive: "#10B981",      // Green - profit
          negative: "#EF4444",      // Red - loss
          neutral: "#9CA3AF",       // Gray - no change
        }
      },
    },
  },
  plugins: [tailwindcssAnimate],
}