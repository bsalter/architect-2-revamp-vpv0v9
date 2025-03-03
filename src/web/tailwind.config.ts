import type { Config } from 'tailwindcss'; // v3.3.3

const config: Config = {
  content: [
    './src/web/pages/**/*.{js,ts,jsx,tsx}',
    './src/web/components/**/*.{js,ts,jsx,tsx}',
    './src/web/app/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    screens: {
      'xs': {'max': '575px'}, // Mobile phones in portrait mode
      'sm': '576px',          // Mobile phones in landscape, small tablets (576px - 767px)
      'md': '768px',          // Tablets in portrait mode (768px - 991px)
      'lg': '992px',          // Tablets in landscape, small desktops (992px - 1199px)
      'xl': '1200px',         // Desktop monitors, large screens (≥1200px)
    },
    extend: {
      colors: {
        // Primary colors from design system
        primary: '#3B82F6',    // Main brand color, primary buttons, active elements
        secondary: '#6B7280',  // Secondary buttons, non-essential UI elements
        success: '#10B981',    // Success messages, positive feedback
        warning: '#F59E0B',    // Warning messages, alerts requiring attention
        danger: '#EF4444',     // Error messages, destructive actions
        background: '#F9FAFB', // Page background, content areas
        surface: '#FFFFFF',    // Cards, dialogs, elevated components
        'text-primary': '#111827',   // Primary text content
        'text-secondary': '#6B7280', // Secondary text, labels, placeholders
        border: '#E5E7EB',     // Element borders, dividers, separators
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      fontSize: {
        // Heading 1: 700 weight, 24-32px
        'h1': ['1.5rem', { lineHeight: '2rem', fontWeight: '700' }],     // 24px
        'h1-lg': ['2rem', { lineHeight: '2.5rem', fontWeight: '700' }],  // 32px
        
        // Heading 2: 600 weight, 20-24px
        'h2': ['1.25rem', { lineHeight: '1.75rem', fontWeight: '600' }],  // 20px
        'h2-lg': ['1.5rem', { lineHeight: '2rem', fontWeight: '600' }],   // 24px
        
        // Heading 3: 600 weight, 16-20px
        'h3': ['1rem', { lineHeight: '1.5rem', fontWeight: '600' }],      // 16px
        'h3-lg': ['1.25rem', { lineHeight: '1.75rem', fontWeight: '600' }], // 20px
        
        // Body: 400 weight, 14-16px
        'body': ['0.875rem', { lineHeight: '1.25rem', fontWeight: '400' }], // 14px
        'body-lg': ['1rem', { lineHeight: '1.5rem', fontWeight: '400' }],   // 16px
        
        // Small Text: 400 weight, 12-14px
        'small': ['0.75rem', { lineHeight: '1rem', fontWeight: '400' }],      // 12px
        'small-lg': ['0.875rem', { lineHeight: '1.25rem', fontWeight: '400' }], // 14px
        
        // Button Text: 500 weight, 14-16px
        'button': ['0.875rem', { lineHeight: '1.25rem', fontWeight: '500' }], // 14px
        'button-lg': ['1rem', { lineHeight: '1.5rem', fontWeight: '500' }],   // 16px
        
        // Input Text: 400 weight, 14-16px
        'input': ['0.875rem', { lineHeight: '1.25rem', fontWeight: '400' }], // 14px
        'input-lg': ['1rem', { lineHeight: '1.5rem', fontWeight: '400' }],   // 16px
      },
      borderRadius: {
        'sm': '0.125rem',  // 2px
        DEFAULT: '0.25rem', // 4px
        'md': '0.375rem',  // 6px
        'lg': '0.5rem',    // 8px
      },
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        DEFAULT: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
      },
      // Additional utilities for AG Grid styling
      backgroundColor: {
        'grid-header': '#F9FAFB',
        'grid-row-hover': '#F3F4F6',
        'grid-row-selected': '#EBF5FF',
      },
      borderColor: {
        'grid-border': '#E5E7EB',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'), // Provides better styling for form elements
  ],
};

export default config;