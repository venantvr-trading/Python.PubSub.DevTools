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

// ============================================
// RISK ANALYSIS MODULE
// ============================================

let riskState = {
    uploadedData: null,
    hmmRegimes: [],
    trainedGANs: {},
    simulations: [],
    currentSimIndex: 0,
    charts: {
        live: null,
        simulation: null,
        histogram: null
    }
};

// Tab switching
function switchMainTab(tabName) {
    document.querySelectorAll('.main-tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.main-tab-content').forEach(content => content.classList.remove('active'));

    event.target.classList.add('active');
    document.getElementById('main-tab-' + tabName).classList.add('active');

    if (tabName === 'risk' && !riskState.charts.live) {
        initRiskCharts();
    }
}

function switchSubTab(tabName) {
    document.querySelectorAll('.sub-tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.sub-tab-content').forEach(content => content.classList.remove('active'));

    event.target.classList.add('active');
    document.getElementById('sub-tab-' + tabName).classList.add('active');
}

// Initialize ApexCharts
function initRiskCharts() {
    // Live candlestick chart
    const liveOptions = {
        series: [{name: 'price', data: []}],
        chart: {type: 'candlestick', height: 400, toolbar: {show: false}},
        xaxis: {type: 'datetime'},
        yaxis: {tooltip: {enabled: true}},
        plotOptions: {
            candlestick: {
                colors: {upward: '#26a69a', downward: '#ef5350'}
            }
        }
    };
    riskState.charts.live = new ApexCharts(document.getElementById('chart-live'), liveOptions);
    riskState.charts.live.render();

    // Simulation chart
    const simOptions = {
        series: [{name: 'close', data: []}],
        chart: {type: 'line', height: 400, toolbar: {show: false}},
        stroke: {curve: 'smooth', width: 2},
        xaxis: {type: 'numeric', title: {text: 'Bougie'}},
        yaxis: {title: {text: 'Prix'}},
        colors: ['#667eea']
    };
    riskState.charts.simulation = new ApexCharts(document.getElementById('chart-simulation'), simOptions);
    riskState.charts.simulation.render();

}

// File upload handler
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file-upload-risk');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileUpload);
    }
});

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const statusDiv = document.getElementById('file-status-risk');
    statusDiv.textContent = `Chargement: ${file.name}...`;

    const reader = new FileReader();
    reader.onload = async function(e) {
        const csvContent = e.target.result;

        try {
            // Upload to backend
            const response = await fetch('/api/risk/upload', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({csv_content: csvContent})
            });

            const result = await response.json();

            if (result.error) {
                statusDiv.textContent = `❌ Erreur: ${result.error}`;
                return;
            }

            const stats = result.stats;
            statusDiv.textContent = `✅ ${stats.count} bougies chargées (${stats.start_date} → ${stats.end_date})`;

            // Display last 200 candles from preview
            if (stats.preview && stats.preview.length > 0) {
                const candles = stats.preview.map(c => ({
                    timestamp: c.timestamp,
                    open: c.open,
                    high: c.high,
                    low: c.low,
                    close: c.close
                }));
                displayLiveChart(candles);
            }

            // Enable HMM button
            document.getElementById('btn-train-hmm').disabled = false;

        } catch (error) {
            statusDiv.textContent = `❌ Erreur: ${error.message}`;
        }
    };
    reader.readAsText(file);
}

function displayLiveChart(candles) {
    const chartData = candles.map(c => ({
        x: new Date(c.timestamp),
        y: [c.open, c.high, c.low, c.close]
    }));

    riskState.charts.live.updateSeries([{data: chartData}]);
}

// HMM Training
document.addEventListener('DOMContentLoaded', function() {
    const btnHmm = document.getElementById('btn-train-hmm');
    if (btnHmm) {
        btnHmm.addEventListener('click', trainHMM);
    }
});

async function trainHMM() {
    const statusDiv = document.getElementById('hmm-status');
    const regimeList = document.getElementById('hmm-regimes');

    statusDiv.textContent = '⏳ Identification des régimes en cours...';
    regimeList.innerHTML = '';

    try {
        const response = await fetch('/api/risk/train_hmm', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });

        const result = await response.json();

        if (result.error) {
            statusDiv.textContent = `❌ Erreur: ${result.error}`;
            return;
        }

        const regimes = result.regimes;
        riskState.hmmRegimes = regimes;
        statusDiv.textContent = `✅ ${regimes.length} régimes identifiés`;

        regimeList.innerHTML = regimes.map(r =>
            `<li style="color: ${r.color};">${r.name} (${(r.prob * 100).toFixed(0)}%)</li>`
        ).join('');

        // Populate GAN dropdown
        const ganSelect = document.getElementById('gan-regime-select');
        ganSelect.innerHTML = '<option>Sélectionner un régime</option>' +
            regimes.map(r => `<option value="${r.id}">${r.name}</option>`).join('');
        ganSelect.disabled = false;
        document.getElementById('btn-train-gan').disabled = false;

        // Show current regime badge
        const currentRegime = regimes[0];
        document.getElementById('current-regime-badge').classList.remove('hidden');
        document.getElementById('regime-name').textContent = currentRegime.name;
        document.getElementById('regime-prob').textContent = (currentRegime.prob * 100).toFixed(0);

    } catch (error) {
        statusDiv.textContent = `❌ Erreur: ${error.message}`;
    }
}

// GAN Training
document.addEventListener('DOMContentLoaded', function() {
    const btnGan = document.getElementById('btn-train-gan');
    if (btnGan) {
        btnGan.addEventListener('click', trainGAN);
    }
});

async function trainGAN() {
    const regimeId = document.getElementById('gan-regime-select').value;
    if (regimeId === 'Sélectionner un régime') return;

    const statusDiv = document.getElementById('gan-status');
    statusDiv.textContent = `⏳ Entraînement du GAN pour régime ${regimeId}...`;

    try {
        const response = await fetch('/api/risk/train_gan', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({regime_id: parseInt(regimeId)})
        });

        const result = await response.json();

        if (result.error) {
            statusDiv.textContent = `❌ Erreur: ${result.error}`;
            return;
        }

        // Poll for completion
        const pollInterval = setInterval(async () => {
            const statusResponse = await fetch(`/api/risk/gan_status/${regimeId}`);
            const statusData = await statusResponse.json();

            if (statusData.status !== 'training') {
                clearInterval(pollInterval);

                if (statusData.error) {
                    statusDiv.textContent = `❌ ${statusData.error}`;
                } else {
                    riskState.trainedGANs[regimeId] = true;
                    statusDiv.textContent = `✅ GAN entraîné pour ${Object.keys(riskState.trainedGANs).length}/${riskState.hmmRegimes.length} régimes`;

                    // Enable simulation button if all GANs trained
                    if (Object.keys(riskState.trainedGANs).length === riskState.hmmRegimes.length) {
                        document.getElementById('btn-run-sim').disabled = false;
                    }
                }
            }
        }, 2000);

    } catch (error) {
        statusDiv.textContent = `❌ Erreur: ${error.message}`;
    }
}

// Monte Carlo Simulation
document.addEventListener('DOMContentLoaded', function() {
    const btnSim = document.getElementById('btn-run-sim');
    if (btnSim) {
        btnSim.addEventListener('click', runSimulation);
    }

    const btnPrev = document.getElementById('btn-prev-sim');
    const btnNext = document.getElementById('btn-next-sim');
    if (btnPrev) btnPrev.addEventListener('click', () => navigateSimulation(-1));
    if (btnNext) btnNext.addEventListener('click', () => navigateSimulation(1));
});

async function runSimulation() {
    const simCount = parseInt(document.getElementById('sim-count').value);
    const horizon = parseInt(document.getElementById('sim-horizon').value);

    const loader = document.getElementById('sim-loader');
    loader.classList.remove('hidden');

    // Determine mode: use GAN if all trained, else GBM
    const allGANsTrained = riskState.hmmRegimes &&
                           Object.keys(riskState.trainedGANs).length === riskState.hmmRegimes.length;
    const mode = allGANsTrained ? 'gan' : 'gbm';

    try {
        const response = await fetch('/api/risk/simulate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                n_scenarios: simCount,
                n_candles: horizon,
                mode: mode
            })
        });

        const result = await response.json();

        loader.classList.add('hidden');

        if (result.error) {
            alert(`❌ Erreur: ${result.error}`);
            return;
        }

        alert(`✅ ${result.n_scenarios} scénarios générés!\nMode: ${result.mode.toUpperCase()}\nFichiers sauvegardés dans replay_data/generated/`);

        // Switch to results tab
        switchSubTab('results');
        document.querySelector('.sub-tab[onclick*="results"]').click();

        // Load generated scenarios for display
        loadGeneratedScenarios(result.files);

    } catch (error) {
        loader.classList.add('hidden');
        alert(`❌ Erreur: ${error.message}`);
    }
}

async function loadGeneratedScenarios(filenames) {
    // Load first few scenarios for preview
    const scenarios = [];

    for (let i = 0; i < Math.min(10, filenames.length); i++) {
        try {
            const response = await fetch(`/replay_data/generated/${filenames[i]}`);
            const data = await response.json();
            scenarios.push(data.candles);
        } catch (error) {
            console.error('Failed to load scenario:', error);
        }
    }

    riskState.simulations = scenarios;
    riskState.currentSimIndex = 0;

    if (scenarios.length > 0) {
        displaySimulation(0);
        document.getElementById('btn-prev-sim').disabled = false;
        document.getElementById('btn-next-sim').disabled = false;
    }
}

function calculateRiskMetrics(sims, startPrice) {
    // Just display first scenario
    displaySimulation(0);
}

function displaySimulation(index) {
    if (!riskState.simulations.length) return;

    const scenario = riskState.simulations[index];

    // Check if scenario is array of candles or array of prices
    let data;
    if (scenario[0] && typeof scenario[0] === 'object' && 'close' in scenario[0]) {
        // Candles format
        data = scenario.map((candle, i) => ({x: i, y: candle.close}));
    } else {
        // Prices array
        data = scenario.map((price, i) => ({x: i, y: price}));
    }

    riskState.charts.simulation.updateSeries([{data: data}]);

    document.getElementById('sim-counter').textContent = `Scénario ${index + 1} / ${riskState.simulations.length}`;
}

function navigateSimulation(direction) {
    riskState.currentSimIndex += direction;

    if (riskState.currentSimIndex < 0) {
        riskState.currentSimIndex = 0;
    } else if (riskState.currentSimIndex >= riskState.simulations.length) {
        riskState.currentSimIndex = riskState.simulations.length - 1;
    }

    displaySimulation(riskState.currentSimIndex);
}
