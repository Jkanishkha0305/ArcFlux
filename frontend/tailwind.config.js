/**
 * ============================================
 * TAILWIND CSS CONFIGURATION
 * ============================================
 * 
 * Tailwind is a utility-first CSS framework.
 * Instead of writing CSS, you use class names like:
 * - "bg-blue-500" = blue background
 * - "text-white" = white text
 * - "p-4" = padding of 1rem
 * 
 * Docs: https://tailwindcss.com/
 */

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563eb', // Blue
        secondary: '#7c3aed', // Purple
        success: '#10b981', // Green
        danger: '#ef4444', // Red
      },
    },
  },
  plugins: [],
};

