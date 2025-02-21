document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('.registration-form');
    const photoInput = document.getElementById('photo');
    const photoPreview = document.querySelector('.photo-preview');
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');

    // Photo preview
    if (photoInput) {
        photoInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    photoPreview.innerHTML = `
                        <img src="${e.target.result}" alt="Preview" style="max-width: 200px; max-height: 200px;">
                    `;
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Form validation
    form.addEventListener('submit', function(e) {
        let isValid = true;
        const errorMessages = [];

        // Email validation
        const email = document.getElementById('email');
        if (email && !isValidEmail(email.value)) {
            isValid = false;
            errorMessages.push('Please enter a valid email address');
            email.classList.add('error');
        }

        // Phone validation
        const phone = document.getElementById('phone');
        if (phone && !isValidPhone(phone.value)) {
            isValid = false;
            errorMessages.push('Please enter a valid 10-digit phone number');
            phone.classList.add('error');
        }

        // Password validation
        if (password.value !== confirmPassword.value) {
            isValid = false;
            errorMessages.push('Passwords do not match');
            password.classList.add('error');
            confirmPassword.classList.add('error');
        }

        if (password.value.length < 8) {
            isValid = false;
            errorMessages.push('Password must be at least 8 characters long');
            password.classList.add('error');
        }

        if (!isValid) {
            e.preventDefault();
            showErrors(errorMessages);
        }
    });

    // Input validation helpers
    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function isValidPhone(phone) {
        return /^[0-9]{10}$/.test(phone);
    }

    function showErrors(messages) {
        const errorDiv = document.querySelector('.error-message') || document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = messages.join('<br>');
        
        if (!document.querySelector('.error-message')) {
            form.insertBefore(errorDiv, form.firstChild);
        }
    }

    // Clear error styling on input
    document.querySelectorAll('input').forEach(input => {
        input.addEventListener('input', function() {
            this.classList.remove('error');
        });
    });
}); 