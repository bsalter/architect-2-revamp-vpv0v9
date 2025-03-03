import type { Config } from 'tailwindcss'; // v3.3.3

/**
 * Tailwind CSS configuration for the Interaction Management System
 * Implements the design system as specified in the technical requirements
 */
export default {
  content: [
    // Include all possible locations of Tailwind classes in the Angular app
    './src/**/*.{html,ts}',
    './src/**/*.component.{html,ts}',
    './src/**/*.directive.ts',
    './src/**/*.pipe.ts',
    './src/index.html',
  ],
  theme: {
    colors: {
      // Base colors
      transparent: 'transparent',
      current: 'currentColor',
      black: '#000000',
      white: '#FFFFFF',
      
      // Design system colors as defined in section 7.7.1
      primary: '#3B82F6',         // Main brand color
      secondary: '#6B7280',       // Secondary elements
      success: '#10B981',         // Success messages
      warning: '#F59E0B',         // Warning messages
      danger: '#EF4444',          // Error messages, destructive actions
      background: '#F9FAFB',      // Page background
      surface: '#FFFFFF',         // Cards, dialogs
      'text-primary': '#111827',  // Primary text
      'text-secondary': '#6B7280', // Secondary text, labels
      border: '#E5E7EB',          // Borders, dividers
      
      // Shades for hover states and variations
      'primary-50': '#EFF6FF',
      'primary-100': '#DBEAFE',
      'primary-200': '#BFDBFE',
      'primary-300': '#93C5FD',
      'primary-400': '#60A5FA',
      'primary-500': '#3B82F6', // Same as primary
      'primary-600': '#2563EB',
      'primary-700': '#1D4ED8',
      'primary-800': '#1E40AF',
      'primary-900': '#1E3A8A',
      
      'gray-50': '#F9FAFB',     // Same as background
      'gray-100': '#F3F4F6',
      'gray-200': '#E5E7EB',    // Same as border
      'gray-300': '#D1D5DB',
      'gray-400': '#9CA3AF',
      'gray-500': '#6B7280',    // Same as secondary
      'gray-600': '#4B5563',
      'gray-700': '#374151',
      'gray-800': '#1F2937',
      'gray-900': '#111827',    // Same as text-primary
    },
    fontFamily: {
      // Inter font family as specified in typography requirements (7.7.2)
      sans: [
        'Inter',
        'ui-sans-serif',
        'system-ui',
        '-apple-system',
        'BlinkMacSystemFont',
        '"Segoe UI"',
        'Roboto',
        '"Helvetica Neue"',
        'Arial',
        '"Noto Sans"',
        'sans-serif',
        '"Apple Color Emoji"',
        '"Segoe UI Emoji"',
        '"Segoe UI Symbol"',
        '"Noto Color Emoji"',
      ],
    },
    fontSize: {
      // Font sizes as per typography requirements
      'xs': '0.75rem',      // 12px
      'sm': '0.875rem',     // 14px - Small Text (12-14px)
      'base': '1rem',       // 16px - Body, Input Text (14-16px)
      'lg': '1.125rem',     // 18px
      'xl': '1.25rem',      // 20px - Heading 3 (16-20px)
      '2xl': '1.5rem',      // 24px - Heading 2 (20-24px)
      '3xl': '1.875rem',    // 30px
      '4xl': '2.25rem',     // 36px - Heading 1 (24-32px)
    },
    fontWeight: {
      // Font weights as per typography requirements
      'normal': '400',      // Body, Input Text
      'medium': '500',      // Button Text
      'semibold': '600',    // Heading 2, Heading 3
      'bold': '700',        // Heading 1
    },
    screens: {
      // Breakpoints as per responsive design specifications (7.6.1)
      'xs': '0',            // Mobile phones in portrait (<576px)
      'sm': '576px',        // Mobile phones in landscape, small tablets (576px-767px)
      'md': '768px',        // Tablets in portrait (768px-991px)
      'lg': '992px',        // Tablets in landscape, small desktops (992px-1199px)
      'xl': '1200px',       // Desktop monitors, large screens (≥1200px)
    },
    extend: {
      spacing: {
        // Custom spacing scale for consistent UI elements
        '0.5': '0.125rem',  // 2px
        '1.5': '0.375rem',  // 6px
        '2.5': '0.625rem',  // 10px
        '3.5': '0.875rem',  // 14px
      },
      // AG Grid compatible styling (7.7.3)
      backgroundColor: {
        'grid-header': '#f3f4f6', // Light gray header for AG Grid
        'grid-row-even': '#ffffff',
        'grid-row-odd': '#f9fafb',
        'grid-row-hover': '#f3f4f6',
      },
      borderWidth: {
        'grid': '1px',
      },
      // Support for animations and transitions
      transitionProperty: {
        'height': 'height',
        'spacing': 'margin, padding',
      },
      // Accessibility focus styles for WCAG compliance (7.9)
      outline: {
        'blue': '2px solid #3B82F6',
      },
      // Z-index scale for proper layering
      zIndex: {
        '0': '0',
        '10': '10',
        '20': '20',
        '30': '30',
        '40': '40',
        '50': '50',
        'auto': 'auto',
      },
      // Contrast ratios ensured for accessibility compliance
      boxShadow: {
        sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        DEFAULT: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
        none: 'none',
      },
    },
  },
  plugins: [
    // Forms plugin for better form element styling
    require('@tailwindcss/forms'),
    // Typography plugin for rich text content styling
    require('@tailwindcss/typography'),
  ],
} satisfies Config;