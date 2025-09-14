document.addEventListener('DOMContentLoaded', function() {
    const contactForm = document.getElementById('contact-form');
    const submitBtn = document.getElementById('submit-btn');
    const submitText = document.getElementById('submit-text');
    const submitIcon = document.getElementById('submit-icon');
    const messageDiv = document.getElementById('contact-message');
    const alertDiv = document.getElementById('contact-alert');

    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading state
            submitBtn.disabled = true;
            submitText.textContent = 'Sending...';
            submitIcon.className = 'fas fa-spinner fa-spin';
            
            // Hide previous messages
            messageDiv.classList.add('hidden');
            
            // Get form data
            const formData = new FormData(contactForm);
            
            // Send AJAX request
            fetch('/contact/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => response.json())
            .then(data => {
                // Show message
                messageDiv.classList.remove('hidden');
                
                if (data.status === 'success') {
                    alertDiv.className = 'p-4 rounded-lg bg-green-100 border border-green-400 text-green-700';
                    alertDiv.innerHTML = '<i class="fas fa-check-circle mr-2"></i>' + data.message;
                    
                    // Reset form
                    contactForm.reset();
                } else {
                    alertDiv.className = 'p-4 rounded-lg bg-red-100 border border-red-400 text-red-700';
                    alertDiv.innerHTML = '<i class="fas fa-exclamation-circle mr-2"></i>' + data.message;
                }
                
                // Scroll to message
                messageDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            })
            .catch(error => {
                console.error('Error:', error);
                messageDiv.classList.remove('hidden');
                alertDiv.className = 'p-4 rounded-lg bg-red-100 border border-red-400 text-red-700';
                alertDiv.innerHTML = '<i class="fas fa-exclamation-circle mr-2"></i>An error occurred. Please try again.';
            })
            .finally(() => {
                // Reset button state
                submitBtn.disabled = false;
                submitText.textContent = 'Send Message';
                submitIcon.className = 'fas fa-paper-plane';
            });
        });
    }

    // Add click handlers for contact info cards to make them interactive
    const contactCards = document.querySelectorAll('[class*="cursor-pointer"]');
    contactCards.forEach(card => {
        card.addEventListener('click', function() {
            const phoneElement = this.querySelector('p:contains("+91")');
            const emailElement = this.querySelector('p:contains("@")');
            
            if (phoneElement && phoneElement.textContent.includes('+91')) {
                window.open('tel:' + phoneElement.textContent.trim());
            } else if (emailElement && emailElement.textContent.includes('@')) {
                window.open('mailto:' + emailElement.textContent.trim());
            }
        });
    });
});