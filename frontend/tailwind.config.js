/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // StepFun 品牌色
        'stepfun': {
          blue: '#165DFF',
          'blue-dark': '#0E42D2',
          'blue-light': '#E8F3FF',
        },
        // 文字颜色
        'text': {
          primary: '#111827',
          secondary: '#6B7280',
          tertiary: '#9CA3AF',
        },
        // 背景颜色
        'bg': {
          light: '#F9FAFB',
          base: '#FFFFFF',
          dark: '#111827',
        },
        // 边框颜色
        border: '#E5E7EB',
        // 状态颜色
        success: '#10B981',
        warning: '#F59E0B',
        error: '#EF4444',
        info: '#3B82F6',
      },
      borderRadius: {
        'sm': '0.375rem',
        'md': '0.5rem',
        'lg': '0.75rem',
        'xl': '1rem',
      },
      boxShadow: {
        'card': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'card-hover': '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif', 'Apple Color Emoji', 'Segoe UI Emoji'],
      },
    },
  },
  plugins: [],
  // 与 Element Plus 兼容
  corePlugins: {
    preflight: false,
  }
}