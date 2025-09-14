document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('enquiry-form');
    const submitBtn = document.getElementById('submit-btn');
    const submitText = document.getElementById('submit-text');
    const loadingSpinner = document.getElementById('loading-spinner');
    const successMessage = document.getElementById('success-message');
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');

    // Check if SKU is provided in URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const sku = urlParams.get('sku');
    const skuContainer = document.getElementById('sku-container');
    
    if (sku) {
        document.getElementById('id_sku').value = sku;
        skuContainer.style.display = 'block';
        // Pre-fill subject if SKU is provided
        const subjectField = document.getElementById('id_subject');
        if (!subjectField.value) {
            subjectField.value = `Enquiry about product ${sku}`;
        }
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Hide previous messages
        successMessage.classList.add('hidden');
        errorMessage.classList.add('hidden');
        
        // Show loading state
        submitBtn.disabled = true;
        submitText.textContent = 'Sending...';
        loadingSpinner.classList.remove('hidden');
        
        try {
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                successMessage.classList.remove('hidden');
                form.reset();
                // Re-populate SKU if it was set
                if (sku) {
                    document.getElementById('id_sku').value = sku;
                }
                // Scroll to success message
                successMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else {
                throw new Error(data.message || 'Something went wrong');
            }
        } catch (error) {
            errorText.textContent = error.message;
            errorMessage.classList.remove('hidden');
            // Scroll to error message
            errorMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } finally {
            // Reset button state
            submitBtn.disabled = false;
            submitText.textContent = 'Send Enquiry';
            loadingSpinner.classList.add('hidden');
        }
    });

    // Form validation enhancements
    const requiredFields = form.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        field.addEventListener('blur', function() {
            if (!this.value.trim()) {
                this.classList.add('border-red-300');
                this.classList.remove('border-gray-300');
            } else {
                this.classList.remove('border-red-300');
                this.classList.add('border-gray-300');
            }
        });
    });
});