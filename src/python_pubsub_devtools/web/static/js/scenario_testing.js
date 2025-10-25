let selectedScenario = null;
let currentTestId = null;
let updateInterval = null;

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

// Restore dark mode state on page load
function restoreDarkMode() {
    const darkMode = localStorage.getItem('darkMode');
    const btn = document.getElementById('dark-mode-btn');
    if (darkMode === 'enabled') {
        document.body.classList.add('dark-mode');
        btn.textContent = '☀️';
    } else {
        btn.textContent = '🌙';
    }
}

// Load scenarios on page load
document.addEventListener('DOMContentLoaded', function() {
    restoreDarkMode();
    loadScenarios();
});

async function loadScenarios() {
    try {
        const response = await fetch('/api/scenarios');
        const scenarios = await response.json();

        const listContainer = document.getElementById('scenarios-list');

        if (scenarios.length === 0) {
            listContainer.innerHTML = '<div style="text-align: center; color: #6c757d; padding: 20px;">No scenarios found. Add YAML files to tools/scenario_testing/scenarios/</div>';
            return;
        }

        listContainer.innerHTML = scenarios.map(s => `
            <div class="scenario-card" onclick="selectScenario('${s.filename}')">
                <div class="scenario-name">${s.name || s.filename}</div>
                <div class="scenario-desc">${s.description || 'No description'}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load scenarios:', error);
    }
}

async function selectScenario(filename) {
    selectedScenario = filename;

    // Update UI
    document.querySelectorAll('.scenario-card').forEach(card => {
        card.classList.remove('selected');
    });
    event.target.closest('.scenario-card').classList.add('selected');

    // Show configuration panel
    document.getElementById('scenario-config').style.display = 'block';
    document.getElementById('no-scenario').style.display = 'none';

    // Load scenario preview
    try {
        const response = await fetch(`/api/scenario/${filename}`);
        const scenario = await response.json();

        document.getElementById('selected-scenario-name').textContent = scenario.name || filename;
        document.getElementById('scenario-preview').textContent = scenario.content;
    } catch (error) {
        console.error('Failed to load scenario:', error);
    }
}

async function runTest() {
    if (!selectedScenario) return;

    const verbose = document.getElementById('verbose-checkbox').checked;
    const recording = document.getElementById('recording-checkbox').checked;

    // Update UI
    document.getElementById('run-btn').disabled = true;
    document.getElementById('stop-btn').disabled = false;
    document.getElementById('status-badge').className = 'status-badge status-running';
    document.getElementById('status-badge').textContent = '● Running';

    // Show results section
    document.getElementById('results-section').style.display = 'block';

    // Clear previous results
    document.getElementById('execution-log').innerHTML = '<div class="log-entry log-info">[INFO] Starting test execution...</div>';

    // Start test
    try {
        const response = await fetch('/api/run', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                scenario: selectedScenario,
                verbose: verbose,
                recording: recording
            })
        });

        const data = await response.json();
        currentTestId = data.test_id;

        // Start polling for updates
        updateInterval = setInterval(updateTestStatus, 500);
    } catch (error) {
        console.error('Failed to start test:', error);
        document.getElementById('execution-log').innerHTML += '<div class="log-entry log-error">[ERROR] Failed to start test</div>';
        resetUI();
    }
}

async function stopTest() {
    if (!currentTestId) return;

    await fetch(`/api/stop/${currentTestId}`, {method: 'POST'});
    resetUI();
}

async function updateTestStatus() {
    if (!currentTestId) return;

    try {
        const response = await fetch(`/api/status/${currentTestId}`);
        const data = await response.json();

        // Update log
        if (data.log && data.log.length > 0) {
            const logContainer = document.getElementById('execution-log');
            logContainer.innerHTML = data.log.map(entry =>
                `<div class="log-entry log-${entry.level}">[${entry.timestamp}] [${entry.level.toUpperCase()}] ${entry.message}</div>`
            ).join('');
            logContainer.scrollTop = logContainer.scrollHeight;
        }

        // If test is complete
        if (data.status !== 'running') {
            clearInterval(updateInterval);
            updateInterval = null;

            // Update results
            document.getElementById('result-status').textContent = data.status.toUpperCase();
            document.getElementById('result-status').className = 'stat-value ' + (data.status === 'passed' ? 'success' : 'error');
            document.getElementById('result-duration').textContent = data.duration_seconds ? data.duration_seconds.toFixed(2) + 's' : '-';
            document.getElementById('result-assertions').textContent = data.assertions_passed + '/' + data.assertions_total;
            document.getElementById('result-events').textContent = data.events_count || 0;

            // Update assertions list
            if (data.assertions && data.assertions.length > 0) {
                document.getElementById('assertions-list').innerHTML = data.assertions.map(a => `
                    <div class="assertion-item ${a.passed ? 'passed' : 'failed'}">
                        <div class="assertion-icon">${a.passed ? '✓' : '✗'}</div>
                        <div style="flex: 1;">
                            <div style="font-weight: 600;">${a.name}</div>
                            <div style="font-size: 0.85em; color: #6c757d;">${a.message}</div>
                        </div>
                    </div>
                `).join('');
            }

            // Update chaos report
            if (data.chaos) {
                document.getElementById('chaos-report').innerHTML = `
                    <div class="chaos-config-title">Chaos Engineering Report</div>
                    <div class="chaos-item">Events Delayed: ${data.chaos.events_delayed || 0}</div>
                    <div class="chaos-item">Events Dropped: ${data.chaos.events_dropped || 0}</div>
                    <div class="chaos-item">Failures Injected: ${data.chaos.failures_injected || 0}</div>
                    <div class="chaos-item">Total Delay: ${data.chaos.total_delay_ms || 0}ms</div>
                `;
            }

            resetUI();
            document.getElementById('status-badge').className = 'status-badge status-' + data.status;
            document.getElementById('status-badge').textContent = '● ' + data.status.toUpperCase();
        }
    } catch (error) {
        console.error('Failed to update status:', error);
        clearInterval(updateInterval);
        resetUI();
    }
}

function resetUI() {
    document.getElementById('run-btn').disabled = false;
    document.getElementById('stop-btn').disabled = true;
}

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    event.target.classList.add('active');
    document.getElementById('tab-' + tabName).classList.add('active');
}

function switchResultTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    event.target.classList.add('active');
    document.getElementById('result-tab-' + tabName).classList.add('active');
}

// Quick start scenario - direct replay on Mock Exchange
async function quickStartScenario(filename) {
    const mode = document.getElementById('quick-mode-select').value;
    const interval = parseFloat(document.getElementById('quick-interval-select').value);

    const payload = {
        filename: filename,
        mode: mode
    };

    if (mode === 'push') {
        payload.interval_seconds = interval;
    }

    try {
        // Call Mock Exchange API (port 5557)
        const response = await fetch('http://localhost:5557/api/replay/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            alert(`✅ Scénario "${filename.replace('.json', '')}" démarré sur Mock Exchange!\nMode: ${mode}\nAllez sur http://localhost:5557 onglet "Bougies" pour voir le graph`);
        } else {
            alert(`❌ Erreur: ${data.error}`);
        }
    } catch (error) {
        alert(`❌ Erreur de connexion à Mock Exchange (port 5557): ${error.message}\nAssurez-vous que Mock Exchange est démarré.`);
    }
}
