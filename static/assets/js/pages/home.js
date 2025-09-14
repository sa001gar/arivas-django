document.addEventListener('DOMContentLoaded', function () {
    // Enhanced Swiper Configuration
    new Swiper('.latest-products-swiper', {
      slidesPerView: 1,
      spaceBetween: 30,
      loop: true,
      autoplay: {
        delay: 4000,
        disableOnInteraction: false,
        pauseOnMouseEnter: true,
      },
      pagination: {
        el: '.swiper-pagination',
        clickable: true,
        dynamicBullets: true,
      },
      navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev',
      },
      effect: 'slide',
      breakpoints: {
        640: {
          slidesPerView: 2,
          spaceBetween: 20,
        },
        768: {
          slidesPerView: 2,
          spaceBetween: 30,
        },
        1024: {
          slidesPerView: 3,
          spaceBetween: 30,
        },
        1280: {
          slidesPerView: 4,
          spaceBetween: 30,
        },
      },
      on: {
        init: function () {
          // Add custom styling to pagination
          const paginationBullets = document.querySelectorAll('.swiper-pagination-bullet');
          paginationBullets.forEach(bullet => {
            bullet.style.backgroundColor = '#D32F2F';
            bullet.style.opacity = '0.3';
          });
        },
        slideChange: function () {
          // Custom animations on slide change
          const activeSlide = document.querySelector('.swiper-slide-active');
          if (activeSlide) {
            activeSlide.classList.add('animate-pulse');
            setTimeout(() => {
              activeSlide.classList.remove('animate-pulse');
            }, 500);
          }
        }
      }
    });

    // Smooth scroll for scroll indicator (without parallax)
    const scrollIndicator = document.querySelector('.animate-bounce');
    if (scrollIndicator) {
      scrollIndicator.addEventListener('click', function() {
        const nextSection = document.querySelector('section:nth-child(2)');
        if (nextSection) {
          nextSection.scrollIntoView({ behavior: 'smooth' });
        }
      });
    }

    // Enhanced hover effects for feature cards (no scroll dependency)
    const featureCards = document.querySelectorAll('.group');
    featureCards.forEach(card => {
      card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-8px) scale(1.02)';
      });
      
      card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0) scale(1)';
      });
    });
  });