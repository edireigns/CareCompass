/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Deep clinical teal for trust/navigation, warm coral only for
        // the one "recommended" signal so it doesn't compete for attention.
          compass: {
            100: "#DBEAFE",
            300: "#93C5FD",
            500: "#3B82F6",
            700: "#1D4ED8",
            900: "#1E3A8A",
            950: "#172554",
          },
        signal: {
          600: "#d1622f",
          500: "#e07a45",
        },
      },
      boxShadow: {
        card: "0 8px 30px rgba(15, 61, 59, 0.06)",
        "card-hover": "0 18px 45px rgba(15, 61, 59, 0.12)",
      },
      backgroundImage: {
        "hero-pattern": "radial-gradient(circle at 20% 20%, rgba(127,196,192,0.22), transparent 34%), radial-gradient(circle at 85% 70%, rgba(224,122,69,0.14), transparent 28%)",
      },
      fontFamily: {
        display: ["'Source Serif 4'", "serif"],
        sans: ["'Inter'", "sans-serif"],
      },
    },
  },
  plugins: [],
};
