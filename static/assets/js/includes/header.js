// Header scroll effect and mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    if (window.AOS) {
        AOS.init({ 
          once: true, 
          duration: 700, 
          easing: 'ease-out-cubic' 
        });
      }
    // Handle scroll effects
    window.addEventListener('scroll', function() {
        const header = document.getElementById('header');
        if (window.scrollY > 0) {
            header.classList.remove('bg-white/95', 'backdrop-blur-sm');
            header.classList.add('bg-white', 'shadow-md');
        } else {
            header.classList.remove('bg-white', 'shadow-md');
            header.classList.add('bg-white/95', 'backdrop-blur-sm');
        }
    });
});

function toggleMobileMenu() {
    const mobileMenu = document.getElementById('mobile-menu');
    const menuIcon = document.getElementById('menu-icon');
    const closeIcon = document.getElementById('close-icon');
    
    mobileMenu.classList.toggle('hidden');
    menuIcon.classList.toggle('hidden');
    closeIcon.classList.toggle('hidden');
    
    // Close products dropdown when menu is toggled
    const mobileProductsDropdown = document.getElementById('mobile-product-categories');
    const chevron = document.getElementById('mobile-products-chevron');
    mobileProductsDropdown.classList.add('hidden');
    chevron.style.transform = 'rotate(0deg)';
}

function closeMobileMenu() {
    const mobileMenu = document.getElementById('mobile-menu');
    const menuIcon = document.getElementById('menu-icon');
    const closeIcon = document.getElementById('close-icon');
    
    mobileMenu.classList.add('hidden');
    menuIcon.classList.remove('hidden');
    closeIcon.classList.add('hidden');
}

function toggleMobileProductsDropdown() {
    const dropdown = document.getElementById('mobile-product-categories');
    const chevron = document.getElementById('mobile-products-chevron');
    
    dropdown.classList.toggle('hidden');
    if (dropdown.classList.contains('hidden')) {
        chevron.style.transform = 'rotate(0deg)';
    } else {
        chevron.style.transform = 'rotate(180deg)';
    }
}


