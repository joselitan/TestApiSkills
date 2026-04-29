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
let currentAuthor = '';
let currentFromDate = '';
let currentToDate = '';
let currentSort = 'newest';
let deleteEntryId = null; // Store ID of entry to delete
const limit = 10; // Number of entries per page

async function loadEntries(page = 1, search = '', author = '', fromDate = '', toDate = '', sort = 'newest') {
    console.log(`📡 Fetching entries for page ${page}...`);
    try {
        const params = new URLSearchParams({ page, limit });
        if (search)   params.set('search', search);
        if (author)   params.set('author', author);
        if (fromDate) params.set('from_date', fromDate);
        if (toDate)   params.set('to_date', toDate);
        if (sort)     params.set('sort', sort);

        const url = `/api/guestbook?${params.toString()}`;
        const response = await fetch(url, {headers});
        console.log('Response status:', response.status);

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.message || `HTTP error! status: ${response.status}`);
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
                <tr class="reactions-row">
                    <td colspan="6">
                        <div class="reactions-cell">
                            <span class="reactions-label">Reactions:</span>
                            <button id="reaction-like-${entry.userId}" class="reaction-btn" onclick="toggleReaction(${entry.userId}, 'like')">👍 <span id="count-like-${entry.userId}">0</span></button>
                            <button id="reaction-love-${entry.userId}" class="reaction-btn" onclick="toggleReaction(${entry.userId}, 'love')">❤️ <span id="count-love-${entry.userId}">0</span></button>
                            <button id="reaction-laugh-${entry.userId}" class="reaction-btn" onclick="toggleReaction(${entry.userId}, 'laugh')">😄 <span id="count-laugh-${entry.userId}">0</span></button>
                        </div>
                    </td>
                </tr>
            `).join('');
            // Load reaction counts for each entry
            entries.forEach(entry => loadReactions(entry.userId));
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
    currentSearch   = document.getElementById('searchInput').value.trim();
    currentAuthor   = document.getElementById('authorInput').value.trim();
    currentFromDate = document.getElementById('fromDate').value;
    currentToDate   = document.getElementById('toDate').value;
    currentSort     = document.getElementById('sortOrder').value;
    currentPage = 1;
    console.log('🔍 Searching with filters:', { currentSearch, currentAuthor, currentFromDate, currentToDate, currentSort });
    renderActiveFilters();
    loadEntries(1, currentSearch, currentAuthor, currentFromDate, currentToDate, currentSort);
}

function clearSearch() {
    currentSearch = currentAuthor = currentFromDate = currentToDate = '';
    currentSort = 'newest';
    currentPage = 1;
    document.getElementById('searchInput').value = '';
    document.getElementById('authorInput').value = '';
    document.getElementById('fromDate').value = '';
    document.getElementById('toDate').value = '';
    document.getElementById('sortOrder').value = 'newest';
    console.log('🧹 Search cleared');
    renderActiveFilters();
    loadEntries(1);
}

function renderActiveFilters() {
    const container = document.getElementById('activeFilters');
    if (!container) return;
    const filters = [];
    if (currentSearch)   filters.push(`<span class="filter-tag">Keyword: "${currentSearch}" <button class="filter-clear" onclick="clearFilter('search')">×</button></span>`);
    if (currentAuthor)   filters.push(`<span class="filter-tag">Author: "${currentAuthor}" <button class="filter-clear" onclick="clearFilter('author')">×</button></span>`);
    if (currentFromDate) filters.push(`<span class="filter-tag">From: ${currentFromDate} <button class="filter-clear" onclick="clearFilter('from')">×</button></span>`);
    if (currentToDate)   filters.push(`<span class="filter-tag">To: ${currentToDate} <button class="filter-clear" onclick="clearFilter('to')">×</button></span>`);
    if (currentSort !== 'newest') filters.push(`<span class="filter-tag">Sort: oldest first <button class="filter-clear" onclick="clearFilter('sort')">×</button></span>`);
    container.innerHTML = filters.join('');
}

function clearFilter(type) {
    if (type === 'search') { currentSearch = ''; document.getElementById('searchInput').value = ''; }
    if (type === 'author') { currentAuthor = ''; document.getElementById('authorInput').value = ''; }
    if (type === 'from')   { currentFromDate = ''; document.getElementById('fromDate').value = ''; }
    if (type === 'to')     { currentToDate = ''; document.getElementById('toDate').value = ''; }
    if (type === 'sort')   { currentSort = 'newest'; document.getElementById('sortOrder').value = 'newest'; }
    currentPage = 1;
    renderActiveFilters();
    loadEntries(1, currentSearch, currentAuthor, currentFromDate, currentToDate, currentSort);
}

function nextPage(){
    loadEntries(currentPage + 1, currentSearch, currentAuthor, currentFromDate, currentToDate, currentSort);
}

function prevPage(){
    if (currentPage > 1) {
        loadEntries(currentPage - 1, currentSearch, currentAuthor, currentFromDate, currentToDate, currentSort);
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
            loadEntries(currentPage, currentSearch, currentAuthor, currentFromDate, currentToDate, currentSort); // Keep current page and filters
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

// ---------------------------------------------------------------------------
// Entry Reactions (DEV-18)
// ---------------------------------------------------------------------------

async function loadReactions(entryId) {
    try {
        const response = await fetch(`/api/entries/${entryId}/reactions`, {headers});
        if (!response.ok) return;
        const data = await response.json();
        const types = ['like', 'love', 'laugh'];
        types.forEach(type => {
            const countEl = document.getElementById(`count-${type}-${entryId}`);
            const btnEl = document.getElementById(`reaction-${type}-${entryId}`);
            if (countEl) countEl.textContent = data[type] ?? 0;
            if (btnEl) {
                if (data.user_reactions && data.user_reactions.includes(type)) {
                    btnEl.classList.add('reaction-active');
                } else {
                    btnEl.classList.remove('reaction-active');
                }
            }
        });
    } catch (err) {
        console.error(`❌ Error loading reactions for entry ${entryId}:`, err);
    }
}

async function toggleReaction(entryId, reactionType) {
    try {
        const response = await fetch(`/api/entries/${entryId}/reactions`, {
            method: 'POST',
            headers,
            body: JSON.stringify({reaction_type: reactionType})
        });
        if (!response.ok) {
            console.error(`❌ Toggle reaction failed: ${response.status}`);
            return;
        }
        // Reload counts and active state for this entry
        await loadReactions(entryId);
    } catch (err) {
        console.error(`❌ Error toggling reaction for entry ${entryId}:`, err);
    }
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
        loadEntries(currentPage, currentSearch, currentAuthor, currentFromDate, currentToDate, currentSort);
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