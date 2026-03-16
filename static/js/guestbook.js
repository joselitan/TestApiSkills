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

let currentPage = 1;
let currentSearch = '';
let deleteEntryId = null; // Store ID of entry to delete
const limit = 10; // Number of entries per page

async function loadEntries(page = 1, search = '') {
    console.log(`📡 Fetching entries for page ${page}${search ? ` with search: "${search}"` : ''}...`);
    try {
        const url = `/api/guestbook?page=${page}&limit=${limit}${search ? `&search=${encodeURIComponent(search)}` : ''}`;
        const response = await fetch(url, {headers});
        console.log('Response status:', response.status);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        const entries = result.data;
        console.log('📦 Entries received:', entries);

        const tbody = document.getElementById('entriesBody');
        if (!tbody) {
            console.error('❌ Table body (entriesBody) not found in DOM');
            return;
        }

        if (entries.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center">No entries found</td></tr>';
        } else {
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
        }
        
        // Update pagination controls
        const pageInfo = document.getElementById('pageInfo');
        const prevBtn = document.querySelector('button[onclick="prevPage()"]');
        const nextBtn = document.querySelector('button[onclick="nextPage()"]');
        
        if (pageInfo && result.meta) {
            pageInfo.innerText = `Page ${result.meta.page} of ${result.meta.pages} (${result.meta.total} total)`;
            currentPage = result.meta.page;
            
            // Enable/disable pagination buttons
            if (prevBtn) {
                prevBtn.disabled = currentPage <= 1;
            }
            if (nextBtn) {
                nextBtn.disabled = currentPage >= result.meta.pages;
            }
        }
        
        console.log('✅ Table updated successfully');

    } catch (error) {
        console.error('❌ Error loading entries:', error);
    }
}

function searchEntries() {
    currentSearch = document.getElementById('searchInput').value;
    currentPage = 1; // Reset to page 1 when searching
    console.log(`🔍 Searching for: "${currentSearch}"`);
    loadEntries(1, currentSearch);
}

function clearSearch() {
    currentSearch = '';
    document.getElementById('searchInput').value = '';
    currentPage = 1;
    console.log('🧹 Search cleared');
    loadEntries(1);
}

function nextPage(){
    loadEntries(currentPage + 1, currentSearch);
}

function prevPage(){
    if (currentPage > 1) {
        loadEntries(currentPage - 1, currentSearch);
    }
}

async function deleteEntry(id) {
    // Fetch entry details to show in modal
    try {
        const response = await fetch(`/api/guestbook/${id}`, {headers});
        const entry = await response.json();
        
        // Store the ID for later use
        deleteEntryId = id;
        
        // Populate modal with entry details
        document.getElementById('deleteEntryName').textContent = entry.name;
        document.getElementById('deleteEntryEmail').textContent = entry.email;
        document.getElementById('deleteEntryComment').textContent = entry.comment || 'No comment';
        
        // Show modal
        document.getElementById('deleteModal').style.display = 'block';
    } catch (error) {
        console.error('❌ Error fetching entry for delete:', error);
    }
}

async function confirmDelete() {
    if (deleteEntryId) {
        console.log(`🗑️ Deleting entry ${deleteEntryId}...`);
        try {
            await fetch(`/api/guestbook/${deleteEntryId}`, {method: 'DELETE', headers});
            closeDeleteModal();
            loadEntries(currentPage, currentSearch); // Keep current page and search
        } catch (error) {
            console.error('❌ Error deleting entry:', error);
        }
    }
}

function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
    deleteEntryId = null;
}

async function editEntry(id) {
    const response = await fetch(`/api/guestbook/${id}`, {headers});
    const entry = await response.json();
    
    // Populate modal with current values
    document.getElementById('editId').value = id;
    document.getElementById('editName').value = entry.name;
    document.getElementById('editEmail').value = entry.email;
    document.getElementById('editComment').value = entry.comment || '';
    
    // Show modal
    document.getElementById('editModal').style.display = 'block';
}

function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
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
    loadEntries(1); // Go to page 1 after import
}

function logout() {
    sessionStorage.removeItem('token');
    window.location.href = '/';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOM Content Loaded');
    
    // Add entry form handler
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
        loadEntries(1); // Go to page 1 after adding new entry
    });

    // Edit form handler
    document.getElementById('editForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('editId').value;
        const data = {
            name: document.getElementById('editName').value,
            email: document.getElementById('editEmail').value,
            comment: document.getElementById('editComment').value
        };
        
        console.log(`✏️ Updating entry ${id}...`);
        await fetch(`/api/guestbook/${id}`, {
            method: 'PUT',
            headers,
            body: JSON.stringify(data)
        });
        
        closeEditModal();
        loadEntries(currentPage, currentSearch);
    });

    // Close modal when clicking outside
    window.onclick = function(event) {
        const editModal = document.getElementById('editModal');
        const deleteModal = document.getElementById('deleteModal');
        
        if (event.target === editModal) {
            closeEditModal();
        }
        if (event.target === deleteModal) {
            closeDeleteModal();
        }
    };

    loadEntries(1); // Load first page on init
});