# Event Flow - Real-Time Architecture Visualization

Visualize your event-driven architecture in real-time. Understand event chains, agent interactions, and system complexity at a glance.

## Overview

Event Flow provides a live, interactive dashboard that displays your system's event architecture as a graph. It works by receiving graph data from a separate scanner tool, which analyzes your codebase to find event publications and subscriptions. This separation allows the visualization server to remain lightweight and independent of your project's code.

## Components

### 1. EventFlowServer

The web dashboard that displays the graphs.

**Features:**

- Interactive SVG graphs with zoom and pan.
- Real-time updates via a REST API.
- Namespace-based filtering and coloring.
- Display of key metrics (total events, agents, connections).
- Multiple graph layouts (`complete`, `full-tree`).

**Launch Server:**

```bash
# Via CLI (recommended)
pubsub-tools event-flow --config devtools_config.yaml

# Programmatically
from python_pubsub_devtools.event_flow import create_app
from python_pubsub_devtools.config import EventFlowConfig

config = EventFlowConfig(port=5555)
app = create_app(config)
app.run()
```

### 2. python-pubsub-scanner (External Library)

A standalone CLI tool that scans your project, generates graph data in DOT format, and POSTs it to the EventFlowServer.

**Features:**

- Static analysis of Python code to find `service_bus.publish` and `service_bus.subscribe` calls.
- Generates graph data with namespace information.
- Can be run manually or in a CI/CD pipeline.

**Usage:**

```bash
# Install the scanner
pip install python-pubsub-scanner

# Run a one-shot scan and push to the API
pubsub-scanner \
    --agents-dir /path/to/your/project/agents \
    --events-dir /path/to/your/project/events \
    --api-url http://localhost:5555
```

## Data Format

The scanner sends data to the server via a `POST` request to `/api/graph`. The JSON payload has the following structure:

```json
{
  "graph_type": "complete",
  "dot_content": "digraph G { ... }",
  "stats": {
    "events": 50,
    "agents": 12,
    "connections": 150
  },
  "namespaces": ["market_data", "position", "risk"]
}
```

## REST API

- `GET /`: Serves the main HTML dashboard.
- `GET /graph/<graph_type>`: Retrieves the specified graph as an SVG image. Accepts filter parameters in the URL query string.
- `POST /api/graph`: Endpoint for the scanner to push new graph data.

## Use Cases

### 1. Onboarding New Developers

Provide an instant, visual map of the system architecture, dramatically reducing the time it takes for new team members to become productive.

### 2. Debugging Complex Event Chains

Quickly trace the path of an event through multiple agents to understand why a business process is failing or behaving unexpectedly.

### 3. Architectural Reviews

Identify architectural smells such as:
- **Orphan Events**: Events that are published but never consumed.
- **Dead-End Agents**: Agents that consume events but never produce any.
- **Circular Dependencies**: Event chains that loop back on themselves.

### 4. Automated Documentation

Integrate the `pubsub-scanner` into your CI/CD pipeline to automatically update the architecture diagram whenever your code changes, ensuring your documentation is never out of date.

## Configuration

Add to your `devtools_config.yaml`:

```yaml
event_flow:
  port: 5555
```

## Architecture

```
┌─────────────────────┐       ┌─────────────────────┐       ┌──────────────────┐
│   Developer's Code  │       │  CI/CD Pipeline     │       │   Web Browser    │
│ (Agents & Events)   │       │ (e.g., GitHub Act)  │       │ (Developer)      │
└──────────┬──────────┘       └──────────┬──────────┘       └────────┬─────────┘
           │                            │                           │ GET /
           ▼                            ▼                           ▼
┌─────────────────────┐       ┌─────────────────────┐       ┌──────────────────┐
│  pubsub-scanner     │──────▶│ POST /api/graph     │       │ EventFlowServer  │
│ (CLI Tool)          │       │                     ├──────▶│ (Flask + Gunicorn) │
└─────────────────────┘       └─────────────────────┘       └──────────────────┘
                                                                    │ GET /graph/...
                                                                    ▼
                                                            ┌──────────────────┐
                                                            │   Graphviz (dot) │
                                                            │ (SVG Conversion) │
                                                            └──────────────────┘
```

## Troubleshooting

### "Graph not found" or "Cache is empty"

This means the Event Flow server has not received any data. You must run the `pubsub-scanner` tool at least once to populate the cache.

```bash
pubsub-scanner --agents-dir /path/to/your/agents --api-url http://localhost:5555
```

### "SVG Conversion Failed"

This error indicates that the `dot` command-line tool is not installed on the system running the `EventFlowServer`.

**Solution:** Install Graphviz.

```bash
# On Debian/Ubuntu
sudo apt-get install graphviz

# On macOS (using Homebrew)
brew install graphviz
```

## Related Tools

- **Event Recorder**: Record and replay event traffic for time-traveling debugging.
- **Scenario Testing**: Define and run complex integration test scenarios.
- **Mock Exchange**: Simulate exchange behavior for testing without real funds.
