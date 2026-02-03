/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0e2a47',    // Azul escuro (Sidebar)
        secondary: '#164e87',  // Azul médio
        accent: '#00d084',     // Verde (Status/Botões)
        background: '#f4f6f8', // Cinza de fundo
        surface: '#ffffff',    // Branco dos cards
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
