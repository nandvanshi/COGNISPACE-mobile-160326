/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#3A5A40",
          foreground: "#FFFFFF",
          50: "#F2F4F3",
          100: "#E8EAE6",
          200: "#C8D1C9",
          300: "#A8B8AB",
          400: "#71917A",
          500: "#3A5A40",
          600: "#344E41",
          700: "#2D4237",
          800: "#263729",
          900: "#1F2C22",
        },
        secondary: {
          DEFAULT: "#D4A373",
          foreground: "#000000",
          50: "#FDFCF8",
          100: "#F9F4ED",
          200: "#F2E8D9",
          300: "#EBDCC5",
          400: "#DFC399",
          500: "#D4A373",
          600: "#BF9368",
          700: "#A07C58",
          800: "#806347",
          900: "#68513A",
        },
        background: "#FDFCF8",
        surface: "#F2F4F3",
        foreground: "#1A1C1A",
        muted: {
          DEFAULT: "#8C968C",
          foreground: "#4A4F4A",
        },
        card: {
          DEFAULT: "#FFFFFF",
          foreground: "#1A1C1A",
        },
        popover: {
          DEFAULT: "#FFFFFF",
          foreground: "#1A1C1A",
        },
        border: "rgba(58, 90, 64, 0.08)",
        input: "#F2F4F3",
        ring: "#3A5A40",
        success: "#588157",
        warning: "#E9C46A",
        error: "#BC4749",
        info: "#457B9D",
      },
      fontFamily: {
        serif: ["'Young Serif'", "serif"],
        sans: ["'Manrope'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      borderRadius: {
        lg: "0.75rem",
        md: "0.5rem",
        sm: "0.25rem",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
