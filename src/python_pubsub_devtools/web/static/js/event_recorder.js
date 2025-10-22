function viewRecording(filename) {
    window.location.href = `/recording/${filename}`;
}

// ============================================================================
// RECORDING CONTROL
// ============================================================================

let recordingStatusInterval = null;

// Show recording modal
function showRecordInfo() {
    const modal = document.getElementById('recording-modal');
    modal.style.display = 'flex';

    // Auto-generate session name with current timestamp
    const now = new Date();
    const timestamp = now.toISOString().replace(/[-:T.]/g, '').slice(0, 15);
    document.getElementById('session-name').value = `session_${timestamp}`;
}

// Close recording modal
function closeRecordingModal() {
    const modal = document.getElementById('recording-modal');
    modal.style.display = 'none';
}

// Start recording
async function startRecording() {
    const sessionName = document.getElementById('session-name').value.trim();

    if (!sessionName) {
        alert('Please enter a session name');
        return;
    }

    try {
        const response = await fetch('/api/record/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({session_name: sessionName})
        });

        const result = await response.json();

        if (response.ok) {
            // Close modal
            closeRecordingModal();

            // Show status bar
            const statusBar = document.getElementById('recording-status-bar');
            statusBar.style.display = 'flex';

            // Update session name
            document.getElementById('recording-session-name').textContent = sessionName;
            document.getElementById('recording-event-count').textContent = '0 events';

            // Change record button to active state
            const recordBtn = document.getElementById('record-btn');
            recordBtn.classList.add('recording-active');
            recordBtn.title = 'Recording in progress...';

            // Start polling for recording status
            recordingStatusInterval = setInterval(updateRecordingStatus, 1000);

            console.log('Recording started:', sessionName);
        } else {
            alert(`Failed to start recording: ${result.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error starting recording:', error);
        alert('Failed to start recording. Make sure DevTools server is running.');
    }
}

// Stop recording
async function stopRecording() {
    if (!confirm('Stop recording and save?')) {
        return;
    }

    try {
        const response = await fetch('/api/record/stop', {
            method: 'POST'
        });

        const result = await response.json();

        if (response.ok) {
            // Hide status bar
            const statusBar = document.getElementById('recording-status-bar');
            statusBar.style.display = 'none';

            // Reset record button
            const recordBtn = document.getElementById('record-btn');
            recordBtn.classList.remove('recording-active');
            recordBtn.title = 'Start Recording';

            // Stop polling
            if (recordingStatusInterval) {
                clearInterval(recordingStatusInterval);
                recordingStatusInterval = null;
            }

            alert(`Recording saved: ${result.filename}\n${result.event_count} events recorded`);

            // Reload page to show new recording
            location.reload();
        } else {
            alert(`Failed to stop recording: ${result.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error stopping recording:', error);
        alert('Failed to stop recording');
    }
}

// Update recording status
async function updateRecordingStatus() {
    try {
        const response = await fetch('/api/record/status');
        const status = await response.json();

        if (status.active) {
            document.getElementById('recording-event-count').textContent = `${status.event_count} events`;
        } else {
            // Recording stopped externally
            const statusBar = document.getElementById('recording-status-bar');
            statusBar.style.display = 'none';

            const recordBtn = document.getElementById('record-btn');
            recordBtn.classList.remove('recording-active');

            if (recordingStatusInterval) {
                clearInterval(recordingStatusInterval);
                recordingStatusInterval = null;
            }
        }
    } catch (error) {
        console.error('Error fetching recording status:', error);
    }
}

// Check recording status on page load
document.addEventListener('DOMContentLoaded', function() {
    checkRecordingStatus();
    checkGlobalReplayStatus();
    // Poll for replay status
    setInterval(checkGlobalReplayStatus, 1000);
});

async function checkRecordingStatus() {
    try {
        const response = await fetch('/api/record/status');
        const status = await response.json();

        if (status.active) {
            // Show status bar
            const statusBar = document.getElementById('recording-status-bar');
            statusBar.style.display = 'flex';

            document.getElementById('recording-session-name').textContent = status.session_name;
            document.getElementById('recording-event-count').textContent = `${status.event_count} events`;

            const recordBtn = document.getElementById('record-btn');
            recordBtn.classList.add('recording-active');

            // Start polling
            recordingStatusInterval = setInterval(updateRecordingStatus, 1000);
        }
    } catch (error) {
        console.error('Error checking recording status:', error);
    }
}

// Show info modal
function showInfo() {
    alert(
        '🎬 Event Recorder Dashboard\n\n' +
        '📊 Features:\n' +
        '• View all recorded sessions\n' +
        '• Analyze event timelines\n' +
        '• Replay recordings (coming soon)\n\n' +
        '⌨️ Keyboard shortcuts:\n' +
        '• D - Toggle dark mode\n' +
        '• Ctrl+R - Refresh\n\n' +
        'For more info, check EVENT_RECORDER_README.md'
    );
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

// ============================================================================
// GLOBAL REPLAY STATUS
// ============================================================================

async function checkGlobalReplayStatus() {
    try {
        const response = await fetch('/api/replay/status');
        const status = await response.json();

        const banner = document.getElementById('replay-status-banner');

        if (status.active) {
            // Show banner
            banner.style.display = 'flex';

            // Update banner content
            const statusText = status.paused ? 'Paused' : 'Replaying';
            const modeText = status.simulation_mode ? '(Simulation)' : '(Publishing to PubSub)';

            document.getElementById('replay-status-text').textContent = `${statusText} ${modeText}`;
            document.getElementById('replay-status-file').textContent = status.filename || '';
            document.getElementById('replay-progress-text').textContent =
                `${status.current_event} / ${status.total_events} events (${Math.round(status.progress)}%)`;

            // Update recording card indicator
            updateRecordingCardReplayIndicator(status);
        } else {
            // Hide banner
            banner.style.display = 'none';

            // Hide all card indicators
            document.querySelectorAll('.recording-card').forEach(card => {
                card.classList.remove('replaying');
                const indicator = card.querySelector('.recording-replay-indicator');
                if (indicator) {
                    indicator.style.display = 'none';
                }
            });
        }
    } catch (error) {
        console.error('Error checking global replay status:', error);
    }
}

function updateRecordingCardReplayIndicator(status) {
    // Find the recording card matching the filename
    const cards = document.querySelectorAll('.recording-card');

    cards.forEach(card => {
        const filename = card.getAttribute('data-filename');
        const indicator = card.querySelector('.recording-replay-indicator');

        if (!indicator) return;

        if (filename === status.filename) {
            // This card is replaying - show indicator
            card.classList.add('replaying');
            indicator.style.display = 'block';

            // Update progress bar
            const fill = indicator.querySelector('.replay-indicator-fill');
            fill.style.width = `${status.progress}%`;

            // Update status text
            const statusText = status.paused ? '⏸️ Paused' : '🎬 Replaying';
            const modeText = status.simulation_mode ? 'Simulation' : 'PubSub';
            indicator.querySelector('.replay-indicator-status').textContent = `${statusText} (${modeText})`;

            // Update progress percentage
            indicator.querySelector('.replay-indicator-progress').textContent =
                `${status.current_event}/${status.total_events} (${Math.round(status.progress)}%)`;
        } else {
            // Hide indicator for other cards
            card.classList.remove('replaying');
            indicator.style.display = 'none';
        }
    });
}

async function stopGlobalReplay() {
    if (!confirm('Stop the current replay?')) {
        return;
    }

    try {
        const response = await fetch('/api/replay/stop', {
            method: 'POST'
        });

        const result = await response.json();

        if (response.ok) {
            console.log('Replay stopped:', result.message);
            // The banner will be hidden by the next status poll
        } else {
            alert(`Failed to stop replay: ${result.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error stopping replay:', error);
        alert('Failed to stop replay');
    }
}
