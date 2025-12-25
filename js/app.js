document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const sessionsGrid = document.getElementById('sessions-grid');
    const searchInput = document.getElementById('search-input');
    const sortButtons = document.querySelectorAll('.btn-sort');
    const themeToggle = document.getElementById('theme-toggle');
    const noResults = document.getElementById('no-results');
    const htmlElement = document.documentElement;
    const themeColorMeta = document.querySelector('meta[name="theme-color"]');

    // Modal Elements
    const modalOverlay = document.getElementById('modal-overlay');
    const modalClose = document.getElementById('modal-close');
    const modalTitle = document.getElementById('modal-title');
    const modalId = document.getElementById('modal-id');
    const modalVideo = document.getElementById('modal-video');
    const modalDownload = document.getElementById('modal-download');
    const modalResources = document.getElementById('modal-resources');
    const modalContent = modalOverlay.querySelector('.modal-content');
    const header = document.querySelector('header');
    const mainContent = document.querySelector('main');
    const footer = document.querySelector('footer');

    // State
    let allSessions = window.SESSIONS_DATA || [];
    let currentFilter = '';
    let currentSort = 'newest';
    let lastFocusedElement = null;
    const STORAGE_KEYS = {
        search: 'sessionsSearch',
        sort: 'sessionsSort'
    };
    const THEME_COLORS = {
        dark: '#202020',
        light: '#f0f0f0'
    };
    const sessionStore = {
        get(key) {
            try {
                return sessionStorage.getItem(key);
            } catch {
                return null;
            }
        },
        set(key, value) {
            try {
                sessionStorage.setItem(key, value);
            } catch {
                // Storage unavailable; skip persistence.
            }
        }
    };

    // Theme Management
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme, false);

    themeToggle.addEventListener('click', () => {
        const currentTheme = htmlElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
    });

    function applyTheme(theme, persist = true) {
        htmlElement.setAttribute('data-theme', theme);
        if (persist) {
            localStorage.setItem('theme', theme);
        }
        if (themeColorMeta) {
            const fallback = THEME_COLORS.dark;
            themeColorMeta.setAttribute('content', THEME_COLORS[theme] || fallback);
        }
    }

    // Initialize UI
    const savedSearch = sessionStore.get(STORAGE_KEYS.search) || '';
    if (savedSearch) {
        searchInput.value = savedSearch;
        currentFilter = savedSearch.toLowerCase();
    }

    const savedSort = sessionStore.get(STORAGE_KEYS.sort);
    if (savedSort && Array.from(sortButtons).some(btn => btn.dataset.sort === savedSort)) {
        currentSort = savedSort;
    }
    sortButtons.forEach(btn => btn.classList.toggle('active', btn.dataset.sort === currentSort));

    renderSessions();

    // Event Listeners
    searchInput.addEventListener('input', (e) => {
        currentFilter = e.target.value.toLowerCase();
        sessionStore.set(STORAGE_KEYS.search, e.target.value);
        renderSessions();
    });

    sortButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update UI
            sortButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update State
            currentSort = btn.dataset.sort;
            sessionStore.set(STORAGE_KEYS.sort, currentSort);
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
        if (e.key === 'Tab' && !modalOverlay.classList.contains('hidden')) {
            handleModalTabKey(e);
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

    function getFocusableElements(container) {
        const focusableSelectors = [
            'a[href]',
            'button:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])'
        ];
        return Array.from(container.querySelectorAll(focusableSelectors.join(','))).filter(
            element => element.offsetParent !== null
        );
    }

    function handleModalTabKey(event) {
        if (!modalContent) return;
        const focusable = getFocusableElements(modalContent);
        if (focusable.length === 0) {
            event.preventDefault();
            modalClose.focus();
            return;
        }
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
        }
    }

    function setBackgroundAriaHidden(isHidden) {
        const targets = [header, mainContent, footer];
        targets.forEach(target => {
            if (!target) return;
            if (isHidden) {
                target.setAttribute('aria-hidden', 'true');
            } else {
                target.removeAttribute('aria-hidden');
            }
        });
    }

    function createSessionCard(session) {
        return `
            <article class="session-card" data-id="${escapeHtml(String(session.id))}">
                <div>
                    <div class="session-id">SESSION ${String(session.id || 0)}</div>
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
        modalId.textContent = `SESSION ${String(session.id)}`;
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
        lastFocusedElement = document.activeElement;
        modalOverlay.classList.remove('hidden');
        modalOverlay.setAttribute('aria-hidden', 'false');
        setBackgroundAriaHidden(true);
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
        modalClose.focus();
    }

    function closeModal() {
        modalOverlay.classList.add('hidden');
        modalOverlay.setAttribute('aria-hidden', 'true');
        setBackgroundAriaHidden(false);
        document.body.style.overflow = '';
        if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
            lastFocusedElement.focus();
        }
        lastFocusedElement = null;
    }
});
