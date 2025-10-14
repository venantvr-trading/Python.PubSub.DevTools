# CLI Usage Guide

The `pubsub-devtools` CLI provides easy access to all DevTools web services.

## Installation

After installing the package, the `pubsub-devtools` command will be available:

```bash
pip install python_pubsub_devtools
```

## Quick Reference

```bash
# View all commands
pubsub-devtools --help

# Launch Event Flow Visualization
pubsub-devtools event-flow --agents-dir ./agents --events-dir ./events

# Launch Event Recorder Dashboard
pubsub-devtools event-recorder --recordings-dir ./recordings

# Launch all services
pubsub-devtools serve-all \
    --agents-dir ./agents \
    --events-dir ./events \
    --recordings-dir ./recordings

# View configuration example
pubsub-devtools config-example
```

## Commands

### event-flow

Launch the Event Flow Visualization service.

**Usage:**
```bash
pubsub-devtools event-flow [OPTIONS]
```

**Required Options:**
- `--agents-dir PATH`: Directory containing agent Python files
- `--events-dir PATH`: Directory containing event JSON files

**Optional Options:**
- `--port INTEGER`: Port to run on (default: 5555)
- `--host TEXT`: Host to bind to (default: 0.0.0.0)
- `--debug / --no-debug`: Enable debug mode (default: enabled)

**Example:**
```bash
pubsub-devtools event-flow \
    --agents-dir /path/to/agents \
    --events-dir /path/to/events \
    --port 5555 \
    --host 0.0.0.0 \
    --debug
```

**What it does:**
- Analyzes agent files to find event publishers and subscribers
- Analyzes event JSON files to extract event metadata
- Generates interactive flow diagrams showing:
  - Who publishes which events
  - Who subscribes to which events
  - Event namespaces and relationships
- Provides web interface at http://localhost:5555

### event-recorder

Launch the Event Recorder Dashboard service.

**Usage:**
```bash
pubsub-devtools event-recorder [OPTIONS]
```

**Required Options:**
- `--recordings-dir PATH`: Directory containing event recording JSON files

**Optional Options:**
- `--port INTEGER`: Port to run on (default: 5556)
- `--host TEXT`: Host to bind to (default: 0.0.0.0)
- `--debug / --no-debug`: Enable debug mode (default: enabled)

**Example:**
```bash
pubsub-devtools event-recorder \
    --recordings-dir /path/to/recordings \
    --port 5556
```

**What it does:**
- Lists all recorded event sessions
- Shows statistics for each recording:
  - Duration
  - Number of events
  - Event frequency
  - Unique event types
- Provides detailed view of individual recordings
- Web interface at http://localhost:5556

### serve-all

Launch all DevTools services simultaneously in parallel.

**Usage:**
```bash
pubsub-devtools serve-all [OPTIONS]
```

**Required Options:**
- `--agents-dir PATH`: Directory containing agent Python files
- `--events-dir PATH`: Directory containing event JSON files
- `--recordings-dir PATH`: Directory containing recording JSON files

**Optional Options:**
- `--event-flow-port INTEGER`: Port for Event Flow (default: 5555)
- `--event-recorder-port INTEGER`: Port for Event Recorder (default: 5556)

**Example:**
```bash
pubsub-devtools serve-all \
    --agents-dir ./agents \
    --events-dir ./events \
    --recordings-dir ./recordings \
    --event-flow-port 5555 \
    --event-recorder-port 5556
```

**What it does:**
- Starts Event Flow service on port 5555
- Starts Event Recorder service on port 5556
- Runs both in parallel using multiprocessing
- Press Ctrl+C to stop all services

**Services Available:**
- Event Flow: http://localhost:5555
- Event Recorder: http://localhost:5556

### config-example

Print an example configuration showing directory structure and usage.

**Usage:**
```bash
pubsub-devtools config-example
```

**What it does:**
- Shows recommended directory structure
- Provides command examples
- Shows Python configuration code

## Directory Structure

Your project should be organized as follows:

```
your-project/
├── agents/              # Agent Python files
│   ├── agent1.py        # Contains publish() and subscribe() calls
│   ├── agent2.py
│   └── agent3.py
├── events/              # Event JSON files
│   ├── EventA.json      # Event metadata and schema
│   ├── EventB.json
│   └── EventC.json
└── recordings/          # Event recording sessions
    ├── session1.json    # Recorded event stream
    └── session2.json
```

### Agents Directory

Contains Python files with event publishers and subscribers:

```python
# agents/market_agent.py
from pubsub import ServiceBus

class MarketAgent:
    def __init__(self, service_bus: ServiceBus):
        self.service_bus = service_bus

        # Subscribe to events
        self.service_bus.subscribe("PriceUpdated", self.on_price_updated)

    def fetch_prices(self):
        # Publish events
        self.service_bus.publish("MarketDataFetched", data, source="market_agent")

    def on_price_updated(self, event):
        # Handle subscribed event
        pass
```

### Events Directory

Contains JSON files describing events:

```json
{
  "name": "MarketDataFetched",
  "namespace": "market_data",
  "description": "Market prices fetched from exchange",
  "schema": {
    "price": "float",
    "timestamp": "datetime"
  }
}
```

### Recordings Directory

Contains recorded event sessions:

```json
{
  "metadata": {
    "session_name": "test_session_1",
    "created_at": "2024-01-01T10:00:00Z"
  },
  "events": [
    {
      "event_name": "MarketDataFetched",
      "timestamp_offset_ms": 0,
      "data": {...}
    },
    {
      "event_name": "PriceUpdated",
      "timestamp_offset_ms": 100,
      "data": {...}
    }
  ]
}
```

## Common Workflows

### Development Workflow

1. **Start Event Flow to visualize your architecture:**
   ```bash
   pubsub-devtools event-flow --agents-dir ./agents --events-dir ./events
   ```

2. **Open http://localhost:5555 in your browser**

3. **Make changes to agents or events**

4. **Refresh the page to see updates**

### Debugging Workflow

1. **Record event session during problematic scenario:**
   ```python
   from python_pubsub_devtools.event_recorder import EventRecorder

   recorder = EventRecorder("./recordings")
   recorder.start_recording("debug_session")
   # Run problematic scenario
   recorder.stop_recording()
   ```

2. **Launch Event Recorder dashboard:**
   ```bash
   pubsub-devtools event-recorder --recordings-dir ./recordings
   ```

3. **Open http://localhost:5556 to analyze the recording**

4. **Replay the session at different speeds to identify issues**

### Testing Workflow

1. **Start all services:**
   ```bash
   pubsub-devtools serve-all \
       --agents-dir ./agents \
       --events-dir ./events \
       --recordings-dir ./recordings
   ```

2. **Run your tests while monitoring in real-time:**
   - Event Flow (http://localhost:5555): See architecture
   - Event Recorder (http://localhost:5556): Browse test recordings

## Tips

### Using with Docker

Create a `docker-compose.yml`:

```yaml
version: '3.8'
services:
  devtools:
    image: python:3.10
    command: >
      bash -c "
        pip install python_pubsub_devtools &&
        pubsub-devtools serve-all
          --agents-dir /app/agents
          --events-dir /app/events
          --recordings-dir /app/recordings
      "
    volumes:
      - ./agents:/app/agents
      - ./events:/app/events
      - ./recordings:/app/recordings
    ports:
      - "5555:5555"
      - "5556:5556"
```

Run with:
```bash
docker-compose up
```

### Running in Background

Use `screen` or `tmux` to keep services running:

```bash
# Start a screen session
screen -S devtools

# Launch services
pubsub-devtools serve-all --agents-dir ./agents --events-dir ./events --recordings-dir ./recordings

# Detach with Ctrl+A, D

# Reattach later
screen -r devtools
```

### Custom Ports

If default ports are in use:

```bash
pubsub-devtools serve-all \
    --agents-dir ./agents \
    --events-dir ./events \
    --recordings-dir ./recordings \
    --event-flow-port 8555 \
    --event-recorder-port 8556
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -i :5555

# Kill the process
kill -9 <PID>

# Or use a different port
pubsub-devtools event-flow --agents-dir ./agents --events-dir ./events --port 5560
```

### Directory Not Found

Make sure directories exist:

```bash
mkdir -p agents events recordings
```

### No Agents/Events Found

Verify file structure:

```bash
# Check agents
ls -la agents/

# Check events
ls -la events/

# Agents should be .py files with publish/subscribe calls
# Events should be .json files with event metadata
```

## Integration with CI/CD

### GitHub Actions

```yaml
name: Visualize Architecture
on: [push]

jobs:
  visualize:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install DevTools
        run: pip install python_pubsub_devtools
      - name: Generate Diagrams
        run: |
          pubsub-devtools event-flow \
            --agents-dir ./agents \
            --events-dir ./events \
            --port 5555 &
          sleep 5
          curl http://localhost:5555/api/graph/simplified > architecture.svg
      - name: Upload Diagram
        uses: actions/upload-artifact@v2
        with:
          name: architecture
          path: architecture.svg
```

## Python API

For programmatic control:

```python
from pathlib import Path
from python_pubsub_devtools.config import DevToolsConfig, EventFlowConfig
from python_pubsub_devtools.event_flow.server import EventFlowServer

# Create configuration
config = EventFlowConfig(
    agents_dir=Path("./agents"),
    events_dir=Path("./events"),
    port=5555
)

# Start server
server = EventFlowServer(config)
server.run(host='0.0.0.0', debug=True)
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/venantvr-trading/Python.PubSub.DevTools/issues
- Documentation: https://github.com/venantvr-trading/Python.PubSub.DevTools/wiki
