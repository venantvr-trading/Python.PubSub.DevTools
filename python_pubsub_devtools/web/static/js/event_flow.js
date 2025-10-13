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

    // Update button icon
    const btn = document.getElementById('fullscreen-btn');
    if (document.body.classList.contains('fullscreen')) {
        btn.textContent = '⛶'; // Exit fullscreen icon
    } else {
        btn.textContent = '⛶'; // Fullscreen icon
    }

    // Save state
    localStorage.setItem('fullscreenMode', document.body.classList.contains('fullscreen'));
}

// Dark mode toggle
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');

    // Update button icon
    const btn = document.getElementById('dark-mode-btn');
    if (document.body.classList.contains('dark-mode')) {
        btn.textContent = '☀️'; // Light mode icon
        localStorage.setItem('darkMode', 'enabled');
    } else {
        btn.textContent = '🌙'; // Dark mode icon
        localStorage.setItem('darkMode', 'disabled');
    }
}

// Restore UI state
function restoreUIState() {
    // Restore filters sidebar state
    const sidebarOpen = localStorage.getItem('filtersSidebarOpen') === 'true';
    if (sidebarOpen) {
        document.getElementById('filters-sidebar').classList.add('open');
        document.getElementById('filters-overlay').classList.add('visible');
    }

    // Restore fullscreen state
    const fullscreen = localStorage.getItem('fullscreenMode') === 'true';
    if (fullscreen) {
        document.body.classList.add('fullscreen');
    }

    // Restore dark mode state
    const darkMode = localStorage.getItem('darkMode');
    const btn = document.getElementById('dark-mode-btn');
    if (darkMode === 'enabled') {
        document.body.classList.add('dark-mode');
        btn.textContent = '☀️';
    } else {
        btn.textContent = '🌙';
    }
}

// Zoom and Pan functionality
let currentZoom = 1;
let currentX = 0;
let currentY = 0;
let isDragging = false;
let startX = 0;
let startY = 0;

// Load SVG content directly into DOM
async function loadSVG(container) {
    const graphType = container.getAttribute('data-graph-type');
    const svgContent = container.querySelector('.svg-content');

    // Get current filters
    const params = new URLSearchParams();

    // Get selected namespaces
    const checkedNamespaces = Array.from(
        document.querySelectorAll('input[name="namespace"]:checked')
    ).map(cb => cb.value);

    checkedNamespaces.forEach(ns => params.append('namespaces', ns));

    // Get hide_failed option
    const hideFailed = document.querySelector('#hide-failed').checked;
    if (hideFailed) {
        params.append('hide_failed', '1');
    }

    // Get hide_rejected option
    const hideRejected = document.querySelector('#hide-rejected').checked;
    if (hideRejected) {
        params.append('hide_rejected', '1');
    }

    try {
        const response = await fetch(`/graph/${graphType}?${params.toString()}`);
        const svgText = await response.text();
        svgContent.innerHTML = svgText;
    } catch (error) {
        console.error('Error loading SVG:', error);
        svgContent.innerHTML = '<p style="color: red;">Error loading graph</p>';
    }
}

async function applyFilters() {
    // Reload all SVGs with new filters
    const containers = document.querySelectorAll('.graph-container');
    for (const container of containers) {
        await loadSVG(container);
    }

    // Save filter state
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
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');

    // Save to localStorage
    localStorage.setItem('lastActiveTab', tabName);

    // Reset zoom for new tab
    currentZoom = 1;
    currentX = 0;
    currentY = 0;
    updateTransform();
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

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // F = Toggle filters
    if (e.key === 'f' || e.key === 'F') {
        e.preventDefault();
        toggleFilters();
    }
    // ESC = Close filters if open
    if (e.key === 'Escape') {
        const sidebar = document.getElementById('filters-sidebar');
        if (sidebar.classList.contains('open')) {
            toggleFilters();
        }
    }
    // Ctrl/Cmd + Shift + F = Toggle fullscreen
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'F') {
        e.preventDefault();
        toggleFullscreen();
    }
    // D = Toggle dark mode
    if (e.key === 'd' || e.key === 'D') {
        e.preventDefault();
        toggleDarkMode();
    }
});

// Setup zoom and pan for all graph containers
document.addEventListener('DOMContentLoaded', async function() {
    // Restore UI state
    restoreUIState();

    // Restore filter state
    restoreFilterState();

    const containers = document.querySelectorAll('.graph-container');

    // Load all SVGs
    for (const container of containers) {
        await loadSVG(container);
    }

    // Restore last active tab
    const lastTab = localStorage.getItem('lastActiveTab') || 'simplified';
    const tabButton = document.querySelector(`button.tab[onclick="showTab('${lastTab}')"]`);
    if (tabButton) {
        tabButton.click();
    }

    // Add real-time filter change listeners
    document.querySelectorAll('input[name="namespace"]').forEach(checkbox => {
        checkbox.addEventListener('change', applyFilters);
    });

    document.querySelector('#hide-failed').addEventListener('change', applyFilters);
    document.querySelector('#hide-rejected').addEventListener('change', applyFilters);

    // Setup interactions
    containers.forEach(container => {
        // Mouse wheel zoom
        container.addEventListener('wheel', function(e) {
            e.preventDefault();

            const delta = e.deltaY;
            const zoomSpeed = 0.001;
            const zoomFactor = 1 - delta * zoomSpeed;

            const newZoom = currentZoom * zoomFactor;
            currentZoom = Math.max(0.1, Math.min(10, newZoom));

            updateTransform();
        });

        // Mouse drag pan
        container.addEventListener('mousedown', function(e) {
            if (e.button === 0) { // Left click only
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

        container.addEventListener('mouseup', function() {
            isDragging = false;
            container.style.cursor = 'grab';
        });

        container.addEventListener('mouseleave', function() {
            isDragging = false;
            container.style.cursor = 'grab';
        });

        // Double click to reset
        container.addEventListener('dblclick', function() {
            resetZoom();
        });
    });
});
