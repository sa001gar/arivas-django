// Tailwind CDN configuration
// window.tailwind = window.tailwind || {};
tailwind.config = {
  theme: {
    extend: {
      colors: {
        'arivas-red': '#D32F2F',
        'arivas-green': '#388E3C',
        'arivas-white': '#FFFFFF',
        'arivas-red-light': '#FFEBEE',
        'arivas-green-light': '#E8F5E8',
        'arivas-gray': '#F5F5F5',
        'arivas-dark': '#212121',
      },
      animation: {
        'slide-in': 'slide-in 0.5s ease-out',
        'fade-in': 'fade-in 0.6s ease-out',
      },
      keyframes: {
        'slide-in': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      boxShadow: {
        premium: '0 10px 30px rgba(0,0,0,0.08)'
      },
      backdropBlur: {
        xs: '2px'
      }
    }
  }
};


