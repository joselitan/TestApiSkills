const resetRequestForm = document.getElementById('resetRequestForm');

if (resetRequestForm) {
    resetRequestForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = document.getElementById('email').value.trim();
        const errorDiv = document.getElementById('error');
        const successDiv = document.getElementById('success');

        errorDiv.textContent = '';
        successDiv.textContent = '';

        if (!email) {
            errorDiv.textContent = 'Please enter your registered email';
            return;
        }

        try {
            const response = await fetch('/api/password-reset-request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const result = await response.json();

            if (response.ok) {
                successDiv.textContent = result.message || 'Reset email sent. Check your inbox.';
                resetRequestForm.reset();
            } else {
                errorDiv.textContent = result.message || 'Unable to send reset email';
            }
        } catch (error) {
            errorDiv.textContent = 'Request failed';
            console.error(error);
        }
    });
}
