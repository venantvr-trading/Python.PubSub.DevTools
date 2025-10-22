document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const uploadStatus = document.getElementById('upload-status');
    const filesTableBody = document.querySelector('#replay-files-table tbody');

    // --- Gestion de l'upload ---
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!fileInput.files.length) {
            showStatus('Veuillez sélectionner un fichier.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        showStatus('Upload en cours...', 'info');

        try {
            const response = await fetch('/api/replay/upload', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                showStatus(result.message, 'success');
                uploadForm.reset();
                await refreshFilesList();
            } else {
                showStatus(result.error || 'Une erreur est survenue.', 'error');
            }
        } catch (error) {
            showStatus('Erreur réseau lors de l\'upload.', 'error');
            console.error('Upload error:', error);
        }
    });

    // --- Gestion de la suppression ---
    filesTableBody.addEventListener('click', async (e) => {
        if (e.target.classList.contains('btn-delete')) {
            handleDelete(e.target);
        } else if (e.target.classList.contains('btn-play')) {
            handlePlay(e.target);
        }
    });

    async function handlePlay(button) {
        const filename = button.dataset.filename;
        showStatus(`Lancement du replay pour "${filename}"...`, 'info');
        try {
            const response = await fetch('/api/replay/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({filename: filename}),
            });
            const result = await response.json();
            showStatus(result.message || result.error, response.ok ? 'success' : 'error');
        } catch (error) {
            showStatus('Erreur réseau lors du lancement du replay.', 'error');
        }
    }

    async function handleDelete(button) {
        const filename = button.dataset.filename;
        if (confirm(`Êtes-vous sûr de vouloir supprimer le fichier "${filename}" ?`)) {
            try {
                const response = await fetch(`/api/replay/files/${filename}`, {
                    method: 'DELETE',
                });
                const result = await response.json();
                if (response.ok) {
                    showStatus(result.message, 'success');
                    await refreshFilesList();
                } else {
                    showStatus(result.error || 'Erreur lors de la suppression.', 'error');
                }
            } catch (error) {
                showStatus('Erreur réseau lors de la suppression.', 'error');
                console.error('Delete error:', error);
            }
        }
    }

    // --- Fonctions utilitaires ---
    function showStatus(message, type) {
        uploadStatus.textContent = message;
        uploadStatus.className = `status-${type}`;
        setTimeout(() => {
            uploadStatus.textContent = '';
            uploadStatus.className = '';
        }, 5000);
    }

    async function refreshFilesList() {
        try {
            const response = await fetch('/api/replay/files');
            const files = await response.json();
            
            filesTableBody.innerHTML = ''; // Vider la liste

            if (files.length > 0) {
                files.forEach(file => {
                    const row = document.createElement('tr');
                    row.dataset.filename = file.filename;
                    row.innerHTML = `
                        <td>${file.filename}</td>
                        <td>${file.size_kb}</td>
                        <td>${new Date(file.created_at * 1000).toLocaleString()}</td>
                        <td>
                            <button class="btn-play" data-filename="${file.filename}" title="Lancer le replay">▶️</button>
                            <button class="btn-delete" data-filename="${file.filename}" title="Supprimer le fichier">🗑️</button>
                        </td>
                    `;
                    filesTableBody.appendChild(row);
                });
            } else {
                filesTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 2rem;">Aucun fichier de replay trouvé. Uploadez-en un pour commencer.</td></tr>';
            }
        } catch (error) {
            console.error('Failed to refresh files list:', error);
            showStatus('Impossible de rafraîchir la liste des fichiers.', 'error');
        }
    }
});
            const filename = e.target.dataset.filename;
            if (confirm(`Êtes-vous sûr de vouloir supprimer le fichier "${filename}" ?`)) {
                try {
                    const response = await fetch(`/api/replay/files/${filename}`, {
                        method: 'DELETE',
                    });
                    const result = await response.json();
                    if (response.ok) {
                        showStatus(result.message, 'success');
                        await refreshFilesList();
                    } else {
                        showStatus(result.error || 'Erreur lors de la suppression.', 'error');
                    }
                } catch (error) {
                    showStatus('Erreur réseau lors de la suppression.', 'error');
                    console.error('Delete error:', error);
                }
            }
        }
    });

    // --- Fonctions utilitaires ---
    function showStatus(message, type) {
        uploadStatus.textContent = message;
        uploadStatus.className = `status-${type}`;
        setTimeout(() => {
            uploadStatus.textContent = '';
            uploadStatus.className = '';
        }, 5000);
    }

    async function refreshFilesList() {
        try {
            const response = await fetch('/api/replay/files');
            const files = await response.json();
            
            filesTableBody.innerHTML = ''; // Vider la liste

            if (files.length > 0) {
                files.forEach(file => {
                    const row = document.createElement('tr');
                    row.dataset.filename = file.filename;
                    row.innerHTML = `
                        <td>${file.filename}</td>
                        <td>${file.size_kb}</td>
                        <td>${new Date(file.created_at * 1000).toLocaleString()}</td>
                        <td>
                            <button class="btn-play" data-filename="${file.filename}" title="Lancer le replay">▶️</button>
                            <button class="btn-delete" data-filename="${file.filename}" title="Supprimer le fichier">🗑️</button>
                        </td>
                    `;
                    filesTableBody.appendChild(row);
                });
            } else {
                filesTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 2rem;">Aucun fichier de replay trouvé. Uploadez-en un pour commencer.</td></tr>';
            }
        } catch (error) {
            console.error('Failed to refresh files list:', error);
            showStatus('Impossible de rafraîchir la liste des fichiers.', 'error');
        }
    }
});
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

    // Update chart colors if exists
    if (typeof candlestickChart !== 'undefined' && candlestickChart) {
        const isDark = document.body.classList.contains('dark-mode');
        candlestickChart.applyOptions({
            layout: {
                background: { color: isDark ? '#1a1a1a' : '#ffffff' },
                textColor: isDark ? '#e0e0e0' : '#333333',
            },
            grid: {
                vertLines: { color: isDark ? '#3a3a3a' : '#e1e1e1' },
                horzLines: { color: isDark ? '#3a3a3a' : '#e1e1e1' },
            },
        });
    }
}

// Restore dark mode preference on page load
document.addEventListener('DOMContentLoaded', function() {
    const darkMode = localStorage.getItem('darkMode');
    if (darkMode === 'enabled') {
        document.body.classList.add('dark-mode');
        document.getElementById('dark-mode-btn').textContent = '☀️';
    }
});
