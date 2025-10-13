let simulationId = null;
let updateInterval = null;
let chart = null;

// Dark mode toggle function
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');

    // Update button icon
    const btn = document.getElementById('dark-mode-btn');
    if (document.body.classList.contains('dark-mode')) {
        btn.textContent = '☀️'; // Light mode icon
        localStorage.setItem('darkMode', 'enabled');
        updateChartColors(true);
    } else {
        btn.textContent = '🌙'; // Dark mode icon
        localStorage.setItem('darkMode', 'disabled');
        updateChartColors(false);
    }
}

// Restore dark mode state on page load
function restoreDarkMode() {
    const darkMode = localStorage.getItem('darkMode');
    const btn = document.getElementById('dark-mode-btn');
    if (darkMode === 'enabled') {
        document.body.classList.add('dark-mode');
        btn.textContent = '☀️';
        updateChartColors(true);
    } else {
        btn.textContent = '🌙';
    }
}

// Update chart colors based on dark mode
function updateChartColors(isDarkMode) {
    if (!chart) return;

    if (isDarkMode) {
        // Dark mode colors
        chart.data.datasets[0].borderColor = '#8fa3f5';
        chart.data.datasets[0].backgroundColor = 'rgba(143, 163, 245, 0.1)';
        chart.options.plugins.legend.labels = {
            color: '#e0e0e0'
        };
        chart.options.scales.x = {
            ticks: { color: '#b0b0b0' },
            grid: { color: 'rgba(255, 255, 255, 0.1)' }
        };
        chart.options.scales.y = {
            beginAtZero: false,
            ticks: { color: '#b0b0b0' },
            grid: { color: 'rgba(255, 255, 255, 0.1)' }
        };
    } else {
        // Light mode colors
        chart.data.datasets[0].borderColor = '#667eea';
        chart.data.datasets[0].backgroundColor = 'rgba(102, 126, 234, 0.1)';
        chart.options.plugins.legend.labels = {
            color: '#666'
        };
        chart.options.scales.x = {
            ticks: { color: '#666' },
            grid: { color: 'rgba(0, 0, 0, 0.1)' }
        };
        chart.options.scales.y = {
            beginAtZero: false,
            ticks: { color: '#666' },
            grid: { color: 'rgba(0, 0, 0, 0.1)' }
        };
    }
    chart.update();
}

// Initialize chart
const ctx = document.getElementById('price-chart').getContext('2d');
chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Price (USDT)',
            data: [],
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            tension: 0.3,
            fill: true
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true
            }
        },
        scales: {
            y: {
                beginAtZero: false
            }
        }
    }
});

// Restore dark mode on page load
restoreDarkMode();

async function startSimulation() {
    const scenario = document.getElementById('scenario').value;
    const initialPrice = parseFloat(document.getElementById('initial_price').value);
    const volatility = parseFloat(document.getElementById('volatility').value);
    const spread = parseInt(document.getElementById('spread').value);

    const response = await fetch('/api/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            scenario: scenario,
            initial_price: initialPrice,
            volatility_multiplier: volatility,
            spread_bps: spread
        })
    });

    const data = await response.json();
    simulationId = data.simulation_id;

    document.getElementById('start-btn').disabled = true;
    document.getElementById('pause-btn').disabled = false;
    document.getElementById('stop-btn').disabled = false;
    document.getElementById('status-badge').className = 'status-badge status-running';
    document.getElementById('status-badge').textContent = '● Running';

    // Reset chart
    chart.data.labels = [];
    chart.data.datasets[0].data = [];
    chart.update();

    // Start polling for updates
    updateInterval = setInterval(updateStats, 500);
}

async function pauseSimulation() {
    if (!simulationId) return;

    await fetch(`/api/pause/${simulationId}`, {method: 'POST'});

    document.getElementById('pause-btn').disabled = true;
    document.getElementById('start-btn').disabled = false;
    document.getElementById('status-badge').className = 'status-badge status-paused';
    document.getElementById('status-badge').textContent = '● Paused';

    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

async function stopSimulation() {
    if (!simulationId) return;

    await fetch(`/api/stop/${simulationId}`, {method: 'POST'});

    document.getElementById('start-btn').disabled = false;
    document.getElementById('pause-btn').disabled = true;
    document.getElementById('stop-btn').disabled = true;
    document.getElementById('status-badge').className = 'status-badge status-stopped';
    document.getElementById('status-badge').textContent = '● Stopped';

    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }

    simulationId = null;
}

async function updateStats() {
    if (!simulationId) return;

    const response = await fetch(`/api/stats/${simulationId}`);
    const data = await response.json();

    if (!data.running) {
        stopSimulation();
        return;
    }

    // Update stats
    document.getElementById('current-price').textContent = '$' + data.current_price.toLocaleString('en-US', {minimumFractionDigits: 2});

    const returnValue = document.getElementById('total-return');
    returnValue.textContent = data.total_return_pct.toFixed(2) + '%';
    returnValue.className = 'stat-value ' + (data.total_return_pct >= 0 ? 'positive' : 'negative');

    document.getElementById('min-price').textContent = '$' + data.min_price.toLocaleString('en-US', {minimumFractionDigits: 2});
    document.getElementById('max-price').textContent = '$' + data.max_price.toLocaleString('en-US', {minimumFractionDigits: 2});
    document.getElementById('volatility-stat').textContent = (data.volatility * 100).toFixed(3) + '%';
    document.getElementById('candle-count').textContent = data.call_count;

    // Update chart (keep last 50 points)
    chart.data.labels.push(data.call_count);
    chart.data.datasets[0].data.push(data.current_price);

    if (chart.data.labels.length > 50) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }

    chart.update('none'); // Update without animation for smooth real-time updates
}

// Keyboard shortcut for dark mode toggle
document.addEventListener('keydown', function(e) {
    // D = Toggle dark mode
    if (e.key === 'd' || e.key === 'D') {
        e.preventDefault();
        toggleDarkMode();
    }
});
