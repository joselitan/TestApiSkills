const registerForm = document.getElementById('registerForm');

if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = document.getElementById('email').value.trim();
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const errorDiv = document.getElementById('error');
        const successDiv = document.getElementById('success');

        errorDiv.textContent = '';
        successDiv.textContent = '';

        if (!email || !password || !confirmPassword) {
            errorDiv.textContent = 'Email and password are required';
            return;
        }
        if (password !== confirmPassword) {
            errorDiv.textContent = 'Passwords do not match';
            return;
        }

        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, username, password, confirm_password: confirmPassword })
            });
            const result = await response.json();

            if (response.ok) {
                successDiv.textContent = result.message || 'Registration successful. Check your email.';
                registerForm.reset();
            } else {
                errorDiv.textContent = result.message || 'Unable to register';
            }
        } catch (error) {
            errorDiv.textContent = 'Registration failed';
            console.error(error);
        }
    });
}
