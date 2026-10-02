/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        compass: {
          100: "#e9f3f8", 200: "#d3e9f2", 300: "#add7e7",
          500: "#338eae", 600: "#167394", 700: "#14617e",
          800: "#174b62", 900: "#123b52", 950: "#102d40",
        },
        signal: {
          600: "#d1622f",
          500: "#e07a45",
        },
      },
      boxShadow: {
        card: "0 8px 28px rgba(16, 45, 64, 0.055)",
        "card-hover": "0 18px 44px rgba(16, 45, 64, 0.12)",
      },
      backgroundImage: {
        "hero-pattern": "radial-gradient(circle at 12% 12%, rgba(105,193,215,0.16), transparent 37%), radial-gradient(circle at 91% 86%, rgba(87,160,186,0.13), transparent 35%)",
      },
      fontFamily: {
        display: ["'Source Serif 4'", "serif"],
        sans: ["'DM Sans'", "sans-serif"],
      },
    },
  },
  plugins: [],
};
