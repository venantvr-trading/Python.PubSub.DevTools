# PubSub Dev Tools

A comprehensive suite of development and debugging tools for PubSub-based event-driven architectures.

## Features

### 🎯 Event Flow Visualization

- Interactive web-based event flow diagrams
- Hierarchical tree and complete graph views
- Namespace filtering and color coding
- Failed/rejected event filtering
- Dark mode support
- GraphViz-powered layout

### 🎬 Event Recorder & Replayer

- Record event streams with timestamps
- Browse recorded sessions via web dashboard
- Filter and analyze event sequences
- Detailed statistics per recording
- Event frequency analysis

### 🧪 Generic Scenario Testing Framework

- Domain-agnostic scenario engine
- Data generation with pluggable profiles
- Chaos injection (delays, failures, data corruption)
- Automated assertion checking
- Multi-phase scenario support
- Comprehensive reporting

## Installation

```bash
pip install python_pubsub_devtools
```

Or install from source:

```bash
git clone <repository>
cd Python.PubSub.DevTools
pip install -e .
```

## Quick Start

### Command Line Usage

The CLI provides commands to launch various DevTools services:

```bash
# View available commands
pubsub-devtools --help

# Launch Event Flow Visualization (port 5555)
pubsub-devtools event-flow \
    --agents-dir ./agents \
    --events-dir ./events \
    --port 5555

# Launch Event Recorder Dashboard (port 5556)
pubsub-devtools event-recorder \
    --recordings-dir ./recordings \
    --port 5556

# Launch all services simultaneously
pubsub-devtools serve-all \
    --agents-dir ./agents \
    --events-dir ./events \
    --recordings-dir ./recordings \
    --event-flow-port 5555 \
    --event-recorder-port 5556

# View example configuration
pubsub-devtools config-example
```

**Available Services:**

- **Event Flow** (port 5555): Visualize event flows between agents
- **Event Recorder** (port 5556): Browse and replay recorded event sessions

### Programmatic Usage

```python
from python_pubsub_devtools import DevToolsConfig, EventFlowServer

# Load configuration
config = DevToolsConfig.from_yaml("devtools_config.yaml")

# Launch event flow server
server = EventFlowServer(config.event_flow)
server.run()
```

## Features Overview

### Event Flow Visualization

Visualize the complete event-driven architecture:

- **Publishers & Subscribers**: See who publishes and subscribes to which events
- **Event Namespaces**: Organize events by namespace with color coding
- **Interactive Diagrams**: Hierarchical tree and complete graph views
- **Filtering**: Filter by namespace, hide failed/rejected events
- **Dark Mode**: Comfortable visualization in any lighting condition
- **GraphViz Layout**: Professional-quality diagram rendering

### Event Recorder

Record and replay event streams for:

- **Debugging**: Analyze complex event sequences
- **Test Fixtures**: Create reproducible test scenarios
- **Performance Analysis**: Track event timing and frequency
- **Session Management**: Browse and compare multiple recordings
- **Statistics**: Event counts, duration, frequency analysis

### Generic Scenario Testing

Build domain-agnostic scenario tests:

- **Data Generation**: Pluggable data generators for any domain
- **Scenario Profiles**: Bull/bear markets, load patterns, failure modes, etc.
- **Chaos Engineering**: Inject delays, failures, data corruption
- **Assertions**: Built-in and custom assertion checkers
- **Multi-Phase**: Complex scenarios with multiple phases
- **Reporting**: Comprehensive test reports with statistics

## Architecture

The library is designed with dependency injection for maximum flexibility:

```
python_pubsub_devtools/
├── config.py              # Configuration management
├── event_flow/            # Event flow analysis and visualization
│   ├── analyzer.py        # Event flow analyzer
│   └── server.py          # Flask web server
├── event_recorder/        # Recording and replaying events
│   └── server.py          # Dashboard for recordings
├── scenario_engine/       # Generic scenario testing framework
│   ├── interfaces.py      # Abstract base classes
│   ├── scenario_engine.py # Core engine
│   ├── assertion_checker.py # Assertion system
│   └── chaos_injector.py  # Chaos engineering
├── web/                   # Shared web assets
│   ├── templates/         # HTML templates
│   └── static/           # CSS, JavaScript, images
└── cli/                   # Command-line interface
    └── main.py           # CLI commands
```

## Dependencies

- Flask >= 2.0.0 (Web interface)
- Click >= 8.0.0 (CLI)
- pydot >= 1.4.0 (Event flow diagrams)
- pandas >= 2.0.0 (Data analysis)
- matplotlib >= 3.5.0 (Visualization)
- networkx >= 2.8.0 (Graph analysis)
- PyYAML >= 6.0 (Configuration)
- Pydantic >= 2.0 (Data validation)

## Development

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Run linters
flake8 python_pubsub_devtools
mypy python_pubsub_devtools
```

## License

MIT License
