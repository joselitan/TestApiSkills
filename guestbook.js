const token = sessionStorage.getItem('token');
if (!token) window.location.href = '/';

const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
};

async function loadEntries() {
    const response = await fetch('/api/guestbook', {headers});
    const entries = await response.json();
    const tbody = document.getElementById('entriesBody');
    tbody.innerHTML = entries.map(entry => `
        <tr>
            <td>${entry.userId}</td>
            <td>${entry.name}</td>
            <td>${entry.email}</td>
            <td>${entry.comment || ''}</td>
            <td>${new Date(entry.created_at).toLocaleString()}</td>
            <td>
                <button onclick="editEntry(${entry.userId})">Edit</button>
                <button onclick="deleteEntry(${entry.userId})">Delete</button>
            </td>
        </tr>
    `).join('');
}

async function deleteEntry(id) {
    if (confirm('Delete this entry?')) {
        await fetch(`/api/guestbook/${id}`, {method: 'DELETE', headers});
        loadEntries();
    }
}

async function editEntry(id) {
    const response = await fetch(`/api/guestbook/${id}`, {headers});
    const entry = await response.json();
    
    const name = prompt('Name:', entry.name);
    const email = prompt('Email:', entry.email);
    const comment = prompt('Comment:', entry.comment);
    
    if (name && email) {
        await fetch(`/api/guestbook/${id}`, {
            method: 'PUT',
            headers,
            body: JSON.stringify({name, email, comment: comment || ''})
        });
        loadEntries();
    }
}

async function importExcel() {
    const fileInput = document.getElementById('excelFile');
    if (!fileInput.files[0]) {
        alert('Please select a file');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    const response = await fetch('/api/guestbook/import', {
        method: 'POST',
        headers: {'Authorization': `Bearer ${token}`},
        body: formData
    });
    
    const result = await response.json();
    alert(result.message);
    fileInput.value = '';
    loadEntries();
}

function logout() {
    sessionStorage.removeItem('token');
    window.location.href = '/';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('entryForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            name: document.getElementById('name').value,
            email: document.getElementById('email').value,
            comment: document.getElementById('comment').value
        };
        
        await fetch('/api/guestbook', {
            method: 'POST',
            headers,
            body: JSON.stringify(data)
        });
        
        e.target.reset();
        loadEntries();
    });

    loadEntries();
});