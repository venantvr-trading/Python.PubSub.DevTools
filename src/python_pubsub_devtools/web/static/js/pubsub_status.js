// PubSub Status Component - Shared JavaScript for status indicator

async function loadPubSubStatus() {
    try {
        const response = await fetch('/api/pubsub/status');
        const data = await response.json();

        const statusDiv = document.getElementById('pubsub-status');
        const statusIcon = statusDiv.querySelector('.status-icon');
        const statusText = statusDiv.querySelector('.status-text');

        if (data.connected) {
            statusDiv.className = 'pubsub-status-indicator connected';
            statusIcon.textContent = '✅';
            statusText.textContent = 'Service Bus connecté';
        } else {
            statusDiv.className = 'pubsub-status-indicator disconnected';
            statusIcon.textContent = '❌';
            statusText.textContent = 'Service Bus déconnecté';
        }
    } catch (error) {
        console.error('Failed to check PubSub status:', error);
        const statusDiv = document.getElementById('pubsub-status');
        const statusIcon = statusDiv.querySelector('.status-icon');
        const statusText = statusDiv.querySelector('.status-text');
        statusDiv.className = 'pubsub-status-indicator disconnected';
        statusIcon.textContent = '❌';
        statusText.textContent = 'Service Bus déconnecté';
    }
}

// Auto-start polling on page load
document.addEventListener('DOMContentLoaded', function() {
    loadPubSubStatus();
    setInterval(loadPubSubStatus, 3000);
});
