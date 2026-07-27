/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}', './public/index.html'],
  theme: {
    extend: {
      // Better Call Saul title-card palette: mustard, burnt orange, teal,
      // rust, against black/cream — the show's signature split-color cards.
      colors: {
        saul: {
          mustard: '#E3A008',
          orange: '#C1440E',
          teal: '#1B998B',
          rust: '#8B3A3A',
          cream: '#F1E6D0',
          black: '#161311',
        },
      },
      fontFamily: {
        display: ['"Bebas Neue"', 'cursive'],
        typewriter: ['"Special Elite"', 'monospace'],
      },
    },
  },
  plugins: [],
}

