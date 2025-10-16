document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    
    // Function to check if passwords match
    function checkPasswords() {
      if (passwordInput.value !== confirmPasswordInput.value) {
        // Show error
        confirmPasswordInput.classList.add('error-border');
        // Check if error message already exists
        let errorElement = confirmPasswordInput.nextElementSibling;
        if (!errorElement || !errorElement.classList.contains('error-message')) {
          errorElement = document.createElement('div');
          errorElement.className = 'error-message';
          confirmPasswordInput.parentNode.insertBefore(errorElement, confirmPasswordInput.nextSibling);
        }
        errorElement.textContent = 'Passwords do not match.';
        return false;
      } else {
        // Remove error
        confirmPasswordInput.classList.remove('error-border');
        const errorElement = confirmPasswordInput.nextElementSibling;
        if (errorElement && errorElement.classList.contains('error-message')) {
          errorElement.remove();
        }
        return true;
      }
    }

    // Check on form submit
    form.addEventListener('submit', function(e) {
      if (!checkPasswords()) {
        e.preventDefault();
      }
    });

    // Also, check on input in confirm_password to remove error message when they start matching
    confirmPasswordInput.addEventListener('input', function() {
      if (passwordInput.value === confirmPasswordInput.value) {
        confirmPasswordInput.classList.remove('error-border');
        const errorElement = confirmPasswordInput.nextElementSibling;
        if (errorElement && errorElement.classList.contains('error-message')) {
          errorElement.remove();
        }
      }
    });
  });