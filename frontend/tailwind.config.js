/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Colores base del tema oscuro
        background: '#0a0a0f',
        surface: '#12121a',
        surfaceHighlight: '#1a1a25',
        
        // Bordes
        border: '#2a2a3a',
        
        // Texto
        text: '#e5e7eb',
        textMuted: '#9ca3af',
        
        // Colores semánticos
        primary: '#6366f1',
        primaryHover: '#818cf8',
        success: '#22c55e',
        warning: '#f59e0b',
        error: '#ef4444',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        lg: '0.5rem',
        md: '0.375rem',
        sm: '0.25rem',
      },
    },
  },
  plugins: [],
}