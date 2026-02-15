console.log('✅ Guestbook script loaded');

const token = sessionStorage.getItem('token');
if (!token) {
    console.warn('❌ No token found, redirecting to login');
    window.location.href = '/';
} else {
    console.log('🔑 Token found in session storage');
}

const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
};

async function loadEntries() {
    console.log('📡 Fetching entries from API...');
    try {
        const response = await fetch('/api/guestbook', {headers});
        console.log('Response status:', response.status);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const entries = await response.json();
        console.log('📦 Entries received:', entries);

        const tbody = document.getElementById('entriesBody');
        if (!tbody) {
            console.error('❌ Table body (entriesBody) not found in DOM');
            return;
        }

        if (entries.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center">No entries found in database</td></tr>';
            return;
        }

        tbody.innerHTML = entries.map(entry => `
            <tr>
                <td>${entry.userId}</td>
                <td>${entry.name}</td>
                <td>${entry.email}</td>
                <td>${entry.comment || ''}</td>
                <td>${new Date(entry.created_at).toLocaleString()}</td>
                <td>
                    <button class="edit-btn" onclick="editEntry(${entry.userId})">Edit</button>
                    <button class="delete-btn" onclick="deleteEntry(${entry.userId})">Delete</button>
                </td>
            </tr>
        `).join('');
        console.log('✅ Table updated successfully');

    } catch (error) {
        console.error('❌ Error loading entries:', error);
    }
}

async function deleteEntry(id) {
    if (confirm('Delete this entry?')) {
        console.log(`🗑️ Deleting entry ${id}...`);
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
        console.log(`✏️ Updating entry ${id}...`);
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
    
    console.log('📂 Uploading Excel file...');
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
    console.log('🚀 DOM Content Loaded');
    document.getElementById('entryForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        console.log('💾 Submitting new entry...');
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