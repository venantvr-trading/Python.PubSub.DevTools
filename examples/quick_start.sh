#!/bin/bash

# Quick Start Script for PubSub DevTools
# This script creates example directories and launches the DevTools services

set -e

echo "======================================================================"
echo "  PubSub DevTools - Quick Start"
echo "======================================================================"
echo ""

# Create example directories if they don't exist
echo "📁 Setting up example directories..."
mkdir -p example_project/agents
mkdir -p example_project/events
mkdir -p example_project/recordings

# Create example agent file
cat > example_project/agents/example_agent.py << 'EOF'
"""
Example Agent demonstrating event publishing and subscription
"""
from typing import Any

class ExampleAgent:
    """Example agent that publishes and subscribes to events"""

    def __init__(self, service_bus):
        self.service_bus = service_bus

        # Subscribe to events
        self.service_bus.subscribe("DataReceived", self.on_data_received)
        self.service_bus.subscribe("ProcessingRequested", self.on_processing_requested)

    def fetch_data(self):
        """Fetch data and publish event"""
        # Simulate data fetching
        data = {"value": 42, "timestamp": "2024-01-01T10:00:00Z"}

        # Publish event
        self.service_bus.publish("DataFetched", data, source="example_agent")

    def process_data(self, data: Any):
        """Process data and publish result"""
        # Simulate processing
        result = {"processed": True, "value": data.get("value", 0) * 2}

        # Publish event
        self.service_bus.publish("DataProcessed", result, source="example_agent")

    def on_data_received(self, event):
        """Handle DataReceived event"""
        print(f"Data received: {event}")
        self.process_data(event.get("data", {}))

    def on_processing_requested(self, event):
        """Handle ProcessingRequested event"""
        print(f"Processing requested: {event}")
        self.fetch_data()
EOF

# Create example event files
cat > example_project/events/DataFetched.json << 'EOF'
{
  "name": "DataFetched",
  "namespace": "data_collection",
  "description": "Data has been fetched from external source",
  "schema": {
    "value": "number",
    "timestamp": "string"
  }
}
EOF

cat > example_project/events/DataProcessed.json << 'EOF'
{
  "name": "DataProcessed",
  "namespace": "data_processing",
  "description": "Data has been processed successfully",
  "schema": {
    "processed": "boolean",
    "value": "number"
  }
}
EOF

cat > example_project/events/DataReceived.json << 'EOF'
{
  "name": "DataReceived",
  "namespace": "data_collection",
  "description": "Data received from agent",
  "schema": {
    "data": "object"
  }
}
EOF

cat > example_project/events/ProcessingRequested.json << 'EOF'
{
  "name": "ProcessingRequested",
  "namespace": "commands",
  "description": "Request to process data",
  "schema": {
    "request_id": "string"
  }
}
EOF

# Create example recording
cat > example_project/recordings/example_session.json << 'EOF'
{
  "metadata": {
    "session_name": "Example Session",
    "created_at": "2024-01-01T10:00:00Z",
    "description": "Example event recording session"
  },
  "events": [
    {
      "event_name": "ProcessingRequested",
      "timestamp_offset_ms": 0,
      "source": "user",
      "data": {
        "request_id": "req_001"
      }
    },
    {
      "event_name": "DataFetched",
      "timestamp_offset_ms": 100,
      "source": "example_agent",
      "data": {
        "value": 42,
        "timestamp": "2024-01-01T10:00:00Z"
      }
    },
    {
      "event_name": "DataReceived",
      "timestamp_offset_ms": 150,
      "source": "system",
      "data": {
        "data": {
          "value": 42
        }
      }
    },
    {
      "event_name": "DataProcessed",
      "timestamp_offset_ms": 250,
      "source": "example_agent",
      "data": {
        "processed": true,
        "value": 84
      }
    }
  ]
}
EOF

echo "✅ Example project created in ./example_project/"
echo ""
echo "Directory structure:"
echo "  example_project/"
echo "  ├── agents/              (1 agent file)"
echo "  ├── events/              (4 event definitions)"
echo "  └── recordings/          (1 example recording)"
echo ""

# Check if pubsub-devtools is installed
if ! command -v pubsub-devtools &> /dev/null; then
    echo "⚠️  pubsub-devtools command not found!"
    echo ""
    echo "Please install the package first:"
    echo "  pip install -e ."
    echo ""
    echo "Or install from PyPI:"
    echo "  pip install python_pubsub_devtools"
    echo ""
    exit 1
fi

echo "======================================================================"
echo "  Launching DevTools Services"
echo "======================================================================"
echo ""
echo "📊 Event Flow:     http://localhost:5555"
echo "🎬 Event Recorder: http://localhost:5556"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""
echo "======================================================================"
echo ""

# Launch all services
pubsub-devtools serve-all \
    --agents-dir example_project/agents \
    --events-dir example_project/events \
    --recordings-dir example_project/recordings \
    --event-flow-port 5555 \
    --event-recorder-port 5556
