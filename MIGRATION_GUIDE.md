# Migration Guide - PubSub Dev Tools

## ✅ Completed Steps

### 1. Library Structure Created

```
Python.PubSub.DevTools/
├── python_pubsub_devtools/           # Main package
│   ├── __init__.py             # Public API
│   ├── config.py               # Configuration & DI
│   ├── event_flow/             # Event flow visualization
│   │   ├── __init__.py
│   │   ├── analyzer.py
│   │   └── hierarchical_tree.py
│   ├── event_recorder/         # Event recording & replay
│   │   ├── __init__.py
│   │   └── recorder.py
│   ├── mock_exchange/          # Market simulation
│   │   ├── __init__.py
│   │   ├── scenario_exchange.py
│   │   └── scenarios.py
│   ├── scenario_testing/       # Scenario testing
│   │   ├── __init__.py
│   │   ├── runner.py
│   │   ├── chaos_injector.py
│   │   ├── assertion_checker.py
│   │   └── schema.py
│   ├── web/                    # Web assets
│   │   ├── templates/          # HTML templates
│   │   │   ├── event_flow.html
│   │   │   ├── event_recorder.html
│   │   │   ├── mock_exchange.html
│   │   │   ├── recording_detail.html
│   │   │   └── scenario_testing.html
│   │   └── static/             # CSS & JS
│   │       ├── css/
│   │       └── js/
│   └── cli/                    # Command-line interface
│       ├── __init__.py
│       └── main.py (TODO)
├── examples/
│   ├── config.example.yaml
│   └── basic_usage.py
├── tests/
├── README.md
├── pyproject.toml
├── setup.py
└── .gitignore
```

### 2. Configuration System

Created `config.py` with dependency injection support:

- `EventFlowConfig`: agents_dir, events_dir, port, test_agents, namespace_colors
- `EventRecorderConfig`: recordings_dir, port
- `MockExchangeConfig`: port, defaults
- `ScenarioTestingConfig`: scenarios_dir, reports_dir, port
- `DevToolsConfig`: Main config class with YAML loading

### 3. Web Assets Migrated

All templates, CSS, and JS files copied to `python_pubsub_devtools/web/`:

- ✅ Templates: 5 HTML files
- ✅ CSS: 5 stylesheets
- ✅ JS: 5 JavaScript files

### 4. Core Modules Migrated

- ✅ Event Flow: analyzer.py, hierarchical_tree.py
- ✅ Event Recorder: recorder.py
- ✅ Mock Exchange: scenario_exchange.py, scenarios.py
- ✅ Scenario Testing: runner.py, chaos_injector.py, assertion_checker.py, schema.py

### 5. Project Configuration Created

Created `devtools_config.yaml` in Python.PubSub.Risk with all paths and settings.

## 🚧 Next Steps to Complete

### 1. Create Server Modules (HIGH PRIORITY)

Need to create server.py files that use Flask with injected configuration:

**a) event_flow/server.py**

```python
from flask import Flask, render_template, Response
from pathlib import Path
from .analyzer import EventFlowAnalyzer
from ..config import EventFlowConfig

class EventFlowServer:
    def __init__(self, config: EventFlowConfig):
        self.config = config
        self.app = self._create_app()

    def _create_app(self):
        # Get package root for web assets
        package_root = Path(__file__).parent.parent
        app = Flask(__name__,
                   template_folder=str(package_root / 'web' / 'templates'),
                   static_folder=str(package_root / 'web' / 'static'))

        @app.route('/')
        def index():
            analyzer = EventFlowAnalyzer(self.config.agents_dir)
            analyzer.analyze()
            # ... implementation
            return render_template('event_flow.html', ...)

        @app.route('/graph/<graph_type>')
        def graph(graph_type):
            # ... implementation
            return Response(svg_content, mimetype='image/svg+xml')

        return app

    def run(self):
        self.app.run(
            host='0.0.0.0',
            port=self.config.port,
            debug=True
        )
```

**b) event_recorder/server.py** - Similar pattern
**c) mock_exchange/server.py** - Similar pattern
**d) scenario_testing/server.py** - Similar pattern

### 2. Create CLI Interface (HIGH PRIORITY)

**cli/main.py**

```python
import argparse
import sys
from pathlib import Path
from python_pubsub_devtools import DevToolsConfig
from python_pubsub_devtools.event_flow.server import EventFlowServer
from python_pubsub_devtools.event_recorder.server import EventRecorderServer
from python_pubsub_devtools.mock_exchange.server import MockExchangeServer
from python_pubsub_devtools.scenario_testing.server import ScenarioTestingServer

def main():
    parser = argparse.ArgumentParser(
        description="PubSub Dev Tools - Development tools for PubSub architectures"
    )
    parser.add_argument(
        '--config', '-c',
        default='devtools_config.yaml',
        help='Path to configuration file'
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Event Flow
    event_flow_parser = subparsers.add_parser('event-flow', help='Launch event flow visualizer')

    # Event Recorder
    recorder_parser = subparsers.add_parser('event-recorder', help='Launch event recorder')

    # Mock Exchange
    exchange_parser = subparsers.add_parser('mock-exchange', help='Launch mock exchange')

    # Scenario Testing
    testing_parser = subparsers.add_parser('test-scenarios', help='Run scenario tests')

    # Dashboard (all services)
    dashboard_parser = subparsers.add_parser('dashboard', help='Launch all dashboards')

    args = parser.parse_args()

    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        return 1

    config = DevToolsConfig.from_yaml(config_path)

    # Execute command
    if args.command == 'event-flow':
        server = EventFlowServer(config.event_flow)
        server.run()
    elif args.command == 'event-recorder':
        server = EventRecorderServer(config.event_recorder)
        server.run()
    # ... etc

    return 0

if __name__ == '__main__':
    sys.exit(main())
```

### 3. Install Library in Editable Mode

```bash
cd /home/rvv/PycharmProjects/venantvr-pubsub/Python.PubSub.DevTools
pip install -e .
```

### 4. Update Python.PubSub.Risk to Use Library

Add to `requirements.txt` or `pyproject.toml`:

```
-e ../Python.PubSub.DevTools
```

Or after publishing to PyPI:

```
python-pubsub-devtools>=0.1.0
```

### 5. Create Migration Scripts (OPTIONAL)

Create scripts in Python.PubSub.Risk to launch tools:

**tools/serve_event_flow_new.py**

```python
from python_pubsub_devtools import DevToolsConfig
from python_pubsub_devtools.event_flow.server import EventFlowServer

config = DevToolsConfig.from_yaml("devtools_config.yaml")
server = EventFlowServer(config.event_flow)
server.run()
```

### 6. Testing

Create tests in `tests/`:

- `test_config.py`: Test configuration loading
- `test_event_flow.py`: Test event flow analyzer
- `test_event_recorder.py`: Test recording/replay
- `test_mock_exchange.py`: Test exchange simulation
- `test_scenario_testing.py`: Test scenario runner

### 7. Documentation

- Update README.md with detailed usage
- Add API documentation
- Create examples for common use cases

## 📝 Usage After Completion

### CLI Usage

```bash
# Launch event flow visualizer
pubsub-tools event-flow

# Launch event recorder
pubsub-tools event-recorder

# Launch mock exchange
pubsub-tools mock-exchange

# Run scenario tests
pubsub-tools test-scenarios --scenario my_scenario.yaml

# Launch all dashboards
pubsub-tools dashboard
```

### Programmatic Usage

```python
from python_pubsub_devtools import DevToolsConfig
from python_pubsub_devtools.event_flow import EventFlowAnalyzer

# Load configuration
config = DevToolsConfig.from_yaml("devtools_config.yaml")

# Use analyzer
analyzer = EventFlowAnalyzer(config.event_flow.agents_dir)
analyzer.analyze()
analyzer.print_summary()
```

## 🎯 Benefits of This Architecture

1. **Complete Decoupling**: No hardcoded paths
2. **Reusable**: Can be used in any PubSub project
3. **Configurable**: All settings via YAML
4. **Installable**: Standard Python package
5. **CLI + API**: Both command-line and programmatic access
6. **Web Assets Included**: Templates/CSS/JS packaged with library

## 📦 Publishing to PyPI (Future)

```bash
cd Python.PubSub.DevTools
python -m build
twine upload dist/*
```

Then in any project:

```bash
pip install python-pubsub-devtools
```

## 🔄 Migration Path for Existing Code

1. Keep old `tools/` directory until migration complete
2. Install new library in editable mode
3. Create new launch scripts using library
4. Test all functionality
5. Once verified, archive old `tools/` directory

## ⚠️ Important Notes

- Web assets paths use `pkg_resources` or `importlib.resources` for packaging
- Configuration file should be in project root
- Recording/scenario/report directories created automatically
- All ports configurable via YAML
