console.log('✅ Login script loaded'); // Check console for this message

const loginForm = document.getElementById('loginForm');

if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        console.log('🖱️ Submit button clicked'); // Check if click is detected

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        try {
            console.log('📡 Sending request to /api/login...');
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });
            
            console.log('Response status:', response.status);

            if (response.ok) {
                const data = await response.json();
                sessionStorage.setItem('token', data.token);
                console.log('🎉 Login successful, redirecting...');
                window.location.href = '/guestbook';
            } else {
                document.getElementById('error').textContent = 'Invalid credentials';
            }
        } catch (error) {
            console.error('❌ Error during login:', error);
            document.getElementById('error').textContent = 'Login failed';
        }
    });
} else {
    console.error('❌ CRITICAL: Login form not found in DOM');
}