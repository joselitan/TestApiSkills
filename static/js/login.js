console.log('✅ Login script loaded'); // Check console for this message

// ==========================================
// AUTHENTICATION CHECK - Redirect authenticated users
// ==========================================
function checkAuthenticationAndRedirect() {
    const token = sessionStorage.getItem('token');
    
    if (token) {
        console.log('🔐 Authenticated user detected on login page, redirecting to /guestbook...');
        window.location.href = '/guestbook';
        return false;
    }
    
    return true;
}

// Run check on page load
if (!checkAuthenticationAndRedirect()) {
    console.log('User is authenticated, blocking login page rendering...');
    document.body.innerHTML = '<p style="text-align: center; margin-top: 20px;">Redirecting...</p>';
}

const loginForm = document.getElementById('loginForm');

if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        console.log('🖱️ Submit button clicked'); // Check if click is detected

        const identifier = document.getElementById('identifier').value.trim();
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('error');

        // Clear previous errors
        errorDiv.textContent = '';

        // Validate required fields
        if (!identifier) {
            errorDiv.textContent = 'Please enter your email or username';
            return;
        }
        if (!password) {
            errorDiv.textContent = 'Please enter your password';
            return;
        }
        
        try {
            console.log('📡 Sending request to /api/login...');
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email: identifier, password})
            });
            
            console.log('Response status:', response.status);
            const result = await response.json();

            if (response.ok) {
                sessionStorage.setItem('token', result.token);
                console.log('🎉 Login successful, redirecting...');
                
                // ==========================================
                // HISTORY MANIPULATION - Remove login page from back button
                // ==========================================
                // Replace the current history entry to skip login page when back button is used
                history.replaceState(null, document.title, '/guestbook');
                
                window.location.href = '/guestbook';
            } else {
                errorDiv.textContent = result.message || 'Invalid credentials';
            }
        } catch (error) {
            console.error('❌ Error during login:', error);
            errorDiv.textContent = 'Login failed';
        }
    });
} else {
    console.error('❌ CRITICAL: Login form not found in DOM');
}
