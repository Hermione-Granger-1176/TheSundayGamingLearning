document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const sessionsGrid = document.getElementById('sessions-grid');
    const searchInput = document.getElementById('search-input');
    const sortButtons = document.querySelectorAll('.btn-sort');
    const themeToggle = document.getElementById('theme-toggle');
    const noResults = document.getElementById('no-results');
    const htmlElement = document.documentElement;

    // Modal Elements
    const modalOverlay = document.getElementById('modal-overlay');
    const modalClose = document.getElementById('modal-close');
    const modalTitle = document.getElementById('modal-title');
    const modalId = document.getElementById('modal-id');
    const modalVideo = document.getElementById('modal-video');
    const modalDownload = document.getElementById('modal-download');
    const modalResources = document.getElementById('modal-resources');

    // State
    let allSessions = window.SESSIONS_DATA || [];
    let currentFilter = '';
    let currentSort = 'newest';

    // Theme Management
    const savedTheme = localStorage.getItem('theme') || 'dark';
    htmlElement.setAttribute('data-theme', savedTheme);

    themeToggle.addEventListener('click', () => {
        const currentTheme = htmlElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        htmlElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });

    // Initialize UI
    renderSessions();

    // Event Listeners
    searchInput.addEventListener('input', (e) => {
        currentFilter = e.target.value.toLowerCase();
        renderSessions();
    });

    sortButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update UI
            sortButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update State
            currentSort = btn.dataset.sort;
            renderSessions();
        });
    });

    // Modal Events
    modalClose.addEventListener('click', closeModal);
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) closeModal();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !modalOverlay.classList.contains('hidden')) {
            closeModal();
        }
    });

    // Utility to prevent XSS
    function escapeHtml(unsafe) {
        if (!unsafe) return "";
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Render Function
    function renderSessions() {
        // Filter
        let filtered = allSessions.filter(session =>
            session.title.toLowerCase().includes(currentFilter)
        );

        // Sort
        filtered.sort((a, b) => {
            // Newest means higher ID
            if (currentSort === 'newest') return b.id - a.id;
            if (currentSort === 'oldest') return a.id - b.id;
            return 0;
        });

        // Toggle No Results
        if (filtered.length === 0) {
            sessionsGrid.innerHTML = '';
            noResults.classList.remove('hidden');
        } else {
            noResults.classList.add('hidden');
            sessionsGrid.innerHTML = filtered.map(session => createSessionCard(session)).join('');

            // Re-attach visual click listeners
            document.querySelectorAll('.session-card').forEach(card => {
                card.addEventListener('click', () => {
                    const id = parseInt(card.dataset.id);
                    const session = allSessions.find(s => s.id === id);
                    if (session) openModal(session);
                });
            });
        }
    }

    function createSessionCard(session) {
        return `
            <article class="session-card" data-id="${escapeHtml(String(session.id))}">
                <div>
                    <div class="session-id">SESSION ${String(session.id || 0).padStart(3, '0')}</div>
                    <h3 class="session-title">${escapeHtml(session.title)}</h3>
                </div>
                <div class="card-cta">
                    <span>View Details</span>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                </div>
            </article>
        `;
    }

    function openModal(session) {
        // Populate Data
        modalId.textContent = `SESSION ${String(session.id).padStart(3, '0')}`;
        modalTitle.textContent = session.title; // textContent handles escaping automatically!
        modalVideo.href = session.video_url;

        // Download setup
        if (session.download_url) {
            modalDownload.href = session.download_url;
            modalDownload.classList.remove('hidden');
        } else {
            modalDownload.classList.add('hidden');
        }

        // Resources setup
        if (session.resources && session.resources.length > 0) {
            const listItems = session.resources.map(res =>
                `<div class="resource-item"><a href="${res.url}" target="_blank" rel="noopener noreferrer">${escapeHtml(res.title)}</a></div>`
            ).join('');
            modalResources.innerHTML = `
                <div style="font-size: 0.85rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 1px;">Material & Resources</div>
                ${listItems}
            `;
        } else {
            modalResources.innerHTML = '';
        }

        // Show Modal
        modalOverlay.classList.remove('hidden');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }

    function closeModal() {
        modalOverlay.classList.add('hidden');
        document.body.style.overflow = '';
    }
});
