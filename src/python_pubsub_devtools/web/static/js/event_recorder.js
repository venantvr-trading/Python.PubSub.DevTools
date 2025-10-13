function viewRecording(filename) {
    window.location.href = `/recording/${filename}`;
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

// Restore dark mode preference on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check for saved dark mode preference
    const darkMode = localStorage.getItem('darkMode');

    if (darkMode === 'enabled') {
        document.body.classList.add('dark-mode');
        const btn = document.getElementById('dark-mode-btn');
        if (btn) {
            btn.textContent = '☀️';
        }
    }
});

// Keyboard shortcut for dark mode (D key)
document.addEventListener('keydown', function(e) {
    if (e.key === 'd' || e.key === 'D') {
        // Only toggle if not typing in an input field
        if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
            e.preventDefault();
            toggleDarkMode();
        }
    }
});
