/**
 * Event Flow Visualization JavaScript
 */

// Filters sidebar toggle
function toggleFilters() {
    const sidebar = document.getElementById('filters-sidebar');
    const overlay = document.getElementById('filters-overlay');

    sidebar.classList.toggle('open');
    overlay.classList.toggle('visible');

    // Save state
    localStorage.setItem('filtersSidebarOpen', sidebar.classList.contains('open'));
}

// Fullscreen toggle
function toggleFullscreen() {
    document.body.classList.toggle('fullscreen');
    const btn = document.getElementById('fullscreen-btn');
    btn.textContent = document.body.classList.contains('fullscreen') ? '↘' : '⛶';
    localStorage.setItem('fullscreenMode', document.body.classList.contains('fullscreen'));
}

// Dark mode toggle
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const btn = document.getElementById('dark-mode-btn');
    if (document.body.classList.contains('dark-mode')) {
        btn.textContent = '☀️';
        localStorage.setItem('darkMode', 'enabled');
    } else {
        btn.textContent = '🌙';
        localStorage.setItem('darkMode', 'disabled');
    }
}

// Restore UI state
function restoreUIState() {
    if (localStorage.getItem('filtersSidebarOpen') === 'true') {
        document.getElementById('filters-sidebar').classList.add('open');
        document.getElementById('filters-overlay').classList.add('visible');
    }
    if (localStorage.getItem('fullscreenMode') === 'true') {
        document.body.classList.add('fullscreen');
        document.getElementById('fullscreen-btn').textContent = '↘';
    }
    if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
        document.getElementById('dark-mode-btn').textContent = '☀️';
    }
}

// Zoom and Pan functionality
let currentZoom = 1;
let currentX = 0;
let currentY = 0;
let isDragging = false;
let startX = 0;
let startY = 0;

async function refreshGraphView(container) {
    /**
     * Récupère l'état actuel des filtres, envoie une requête POST au serveur
     * et met à jour le contenu SVG du conteneur.
     */
    const graphType = container.getAttribute('data-graph-type');
    const svgContent = container.querySelector('.svg-content');

    svgContent.innerHTML = '<p style="padding: 20px; text-align: center; color: #667eea;">Chargement du graphe filtré...</p>';

    // 1. Récupérer les filtres
    const selectedNamespaces = Array.from(
        document.querySelectorAll('input[name="namespace"]:checked')
    ).map(cb => cb.value);

    const keywordsToHide = [];
    if (document.querySelector('#hide-failed').checked) {
        // Le nom de l'input est hide_failed mais le label dit Masquer
        // ce qui est ambigu. On va suivre l'id. Si coché, on masque.
        keywordsToHide.push('Failed');
    }
    if (document.querySelector('#hide-rejected').checked) {
        keywordsToHide.push('Rejected');
    }

    const filters = {
        namespaces: selectedNamespaces,
        keywords: keywordsToHide,
    };

    // 2. Envoyer la requête POST
    try {
        const response = await fetch(`/api/graph/filtered/${graphType}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(filters),
        });

        if (!response.ok) {
            throw new Error(`Erreur du serveur: ${response.status} ${response.statusText}`);
        }

        const svgText = await response.text();
        svgContent.innerHTML = svgText;

    } catch (error) {
        console.error('Erreur lors du chargement du graphe filtré:', error);
        svgContent.innerHTML = `<p style="color: red; padding: 20px;">Erreur lors du chargement du graphe : ${error.message}</p>`;
    }
}

function applyAndSaveFilters() {
    /** Applique les filtres et sauvegarde leur état. */
    const activeTab = document.querySelector('.tab-content.active');
    if (activeTab) {
        const container = activeTab.querySelector('.graph-container');
        if (container) {
            refreshGraphView(container);
        }
    }
    saveFilterState();
}

function selectAllNamespaces() {
    document.querySelectorAll('input[name="namespace"]').forEach(cb => {
        cb.checked = true;
    });
}

function deselectAllNamespaces() {
    document.querySelectorAll('input[name="namespace"]').forEach(cb => {
        cb.checked = false;
    });
}

function saveFilterState() {
    const checkedNamespaces = Array.from(
        document.querySelectorAll('input[name="namespace"]:checked')
    ).map(cb => cb.value);
    const hideFailed = document.querySelector('#hide-failed').checked;
    const hideRejected = document.querySelector('#hide-rejected').checked;

    localStorage.setItem('filterNamespaces', JSON.stringify(checkedNamespaces));
    localStorage.setItem('filterHideFailed', hideFailed);
    localStorage.setItem('filterHideRejected', hideRejected);
}

function restoreFilterState() {
    const savedNamespaces = localStorage.getItem('filterNamespaces');
    const savedHideFailed = localStorage.getItem('filterHideFailed');
    const savedHideRejected = localStorage.getItem('filterHideRejected');

    if (savedNamespaces) {
        const namespaces = JSON.parse(savedNamespaces);
        document.querySelectorAll('input[name="namespace"]').forEach(cb => {
            cb.checked = namespaces.includes(cb.value);
        });
    }

    if (savedHideFailed !== null) {
        document.querySelector('#hide-failed').checked = savedHideFailed === 'true';
    }

    if (savedHideRejected !== null) {
        document.querySelector('#hide-rejected').checked = savedHideRejected === 'true';
    }
}

function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));

    document.getElementById(tabName).classList.add('active');
    // Cible le bouton qui a été cliqué
    const clickedTabButton = document.querySelector(`button.tab[onclick="showTab('${tabName}')"]`);
    if(clickedTabButton) {
        clickedTabButton.classList.add('active');
    }

    localStorage.setItem('lastActiveTab', tabName);

    const newActiveTab = document.getElementById(tabName);
    const container = newActiveTab.querySelector('.graph-container');
    if (container) {
        refreshGraphView(container);
    }

    resetZoom();
}

function zoomIn() {
    currentZoom = Math.min(currentZoom * 1.2, 10);
    updateTransform();
}

function zoomOut() {
    currentZoom = Math.max(currentZoom / 1.2, 0.1);
    updateTransform();
}

function resetZoom() {
    currentZoom = 1;
    currentX = 0;
    currentY = 0;
    updateTransform();
}

function updateTransform() {
    const activeTab = document.querySelector('.tab-content.active');
    if (!activeTab) return;

    const container = activeTab.querySelector('.graph-container');
    if (!container) return;

    const svgContent = container.querySelector('.svg-content');
    if (!svgContent) return;

    svgContent.style.transform = `translate(${currentX}px, ${currentY}px) scale(${currentZoom})`;
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'f' || e.key === 'F') { e.preventDefault(); toggleFilters(); }
    if (e.key === 'Escape' && document.getElementById('filters-sidebar').classList.contains('open')) { toggleFilters(); }
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'F' || e.key ==='f')) { e.preventDefault(); toggleFullscreen(); }
    if (e.key === 'd' || e.key === 'D') { e.preventDefault(); toggleDarkMode(); }
});

document.addEventListener('DOMContentLoaded', async function() {
    restoreUIState();
    restoreFilterState();

    const lastTab = localStorage.getItem('lastActiveTab') || 'complete';
    const tabButton = document.querySelector(`button.tab[onclick="showTab('${lastTab}')"]`);
    if (tabButton) {
        tabButton.click();
    } else {
        const firstContainer = document.querySelector('.graph-container');
        if (firstContainer) {
            refreshGraphView(firstContainer);
        }
    }

    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', applyAndSaveFilters);
    });

    document.querySelector('button[onclick="selectAllNamespaces()"]').addEventListener('click', () => {
        selectAllNamespaces();
        applyAndSaveFilters();
    });
    document.querySelector('button[onclick="deselectAllNamespaces()"]').addEventListener('click', () => {
        deselectAllNamespaces();
        applyAndSaveFilters();
    });

    document.querySelectorAll('.graph-container').forEach(container => {
        container.addEventListener('wheel', function(e) {
            e.preventDefault();
            const delta = e.deltaY;
            const zoomSpeed = 0.001;
            const zoomFactor = 1 - delta * zoomSpeed;
            currentZoom = Math.max(0.1, Math.min(10, currentZoom * zoomFactor));
            updateTransform();
        });

        container.addEventListener('mousedown', function(e) {
            if (e.button === 0) {
                isDragging = true;
                startX = e.clientX - currentX;
                startY = e.clientY - currentY;
                container.style.cursor = 'grabbing';
            }
        });

        container.addEventListener('mousemove', function(e) {
            if (isDragging) {
                currentX = e.clientX - startX;
                currentY = e.clientY - startY;
                updateTransform();
            }
        });

        const stopDragging = () => {
            isDragging = false;
            container.style.cursor = 'grab';
        };

        container.addEventListener('mouseup', stopDragging);
        container.addEventListener('mouseleave', stopDragging);
        container.addEventListener('dblclick', resetZoom);
    });
});