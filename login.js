document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        
        if (response.ok) {
            const data = await response.json();
            sessionStorage.setItem('token', data.token);
            window.location.href = '/guestbook';
        } else {
            document.getElementById('error').textContent = 'Invalid credentials';
        }
    } catch (error) {
        document.getElementById('error').textContent = 'Login failed';
    }
});