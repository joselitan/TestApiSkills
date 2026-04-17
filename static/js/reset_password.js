const resetForm = document.getElementById('resetForm');

function getQueryParam(name) {
    const search = window.location.search.substring(1);
    const params = new URLSearchParams(search);
    return params.get(name);
}

if (resetForm) {
    const token = getQueryParam('token');
    const errorDiv = document.getElementById('error');
    const successDiv = document.getElementById('success');

    if (!token) {
        errorDiv.textContent = 'Password reset token is required.';
    }

    resetForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        errorDiv.textContent = '';
        successDiv.textContent = '';

        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (!password || !confirmPassword) {
            errorDiv.textContent = 'Please enter and confirm your new password.';
            return;
        }
        if (password !== confirmPassword) {
            errorDiv.textContent = 'Passwords do not match.';
            return;
        }

        try {
            const response = await fetch('/api/password-reset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, password, confirm_password: confirmPassword })
            });
            const result = await response.json();

            if (response.ok) {
                successDiv.textContent = result.message || 'Your password has been reset.';
                resetForm.reset();
            } else {
                errorDiv.textContent = result.message || 'Unable to reset password';
            }
        } catch (error) {
            errorDiv.textContent = 'Password reset failed.';
            console.error(error);
        }
    });
}
