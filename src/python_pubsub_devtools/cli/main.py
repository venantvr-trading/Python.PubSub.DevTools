"""
CLI for launching PubSub DevTools web services
"""
import sys
from pathlib import Path
from typing import Optional

import click

from ..config import DevToolsConfig
from ..event_flow.server import EventFlowServer
from ..event_recorder.server import EventRecorderServer


@click.group()
@click.version_option()
def cli():
    """
    PubSub DevTools CLI

    Launch web services for event flow visualization, event recording, and more.
    """
    pass


@cli.command()
@click.option(
    '--agents-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help='Path to directory containing agent Python files'
)
@click.option(
    '--events-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help='Path to directory containing event JSON files'
)
@click.option(
    '--port',
    type=int,
    default=5555,
    help='Port to run the server on (default: 5555)'
)
@click.option(
    '--host',
    type=str,
    default='0.0.0.0',
    help='Host to bind to (default: 0.0.0.0)'
)
@click.option(
    '--debug/--no-debug',
    default=True,
    help='Enable debug mode (default: enabled)'
)
def event_flow(
    agents_dir: Path,
    events_dir: Path,
    port: int,
    host: str,
    debug: bool
):
    """
    Launch the Event Flow Visualization service.

    Visualizes the flow of events between agents in your system.
    """
    from ..config import EventFlowConfig

    config = EventFlowConfig(
        agents_dir=agents_dir,
        events_dir=events_dir,
        port=port
    )

    server = EventFlowServer(config)
    try:
        server.run(host=host, debug=debug)
    except KeyboardInterrupt:
        click.echo("\n👋 Event Flow server stopped")
        sys.exit(0)


@cli.command()
@click.option(
    '--recordings-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help='Path to directory containing event recording JSON files'
)
@click.option(
    '--port',
    type=int,
    default=5556,
    help='Port to run the server on (default: 5556)'
)
@click.option(
    '--host',
    type=str,
    default='0.0.0.0',
    help='Host to bind to (default: 0.0.0.0)'
)
@click.option(
    '--debug/--no-debug',
    default=True,
    help='Enable debug mode (default: enabled)'
)
def event_recorder(
    recordings_dir: Path,
    port: int,
    host: str,
    debug: bool
):
    """
    Launch the Event Recorder Dashboard service.

    Browse and replay recorded event sessions.
    """
    from ..config import EventRecorderConfig

    config = EventRecorderConfig(
        recordings_dir=recordings_dir,
        port=port
    )

    server = EventRecorderServer(config)
    try:
        server.run(host=host, debug=debug)
    except KeyboardInterrupt:
        click.echo("\n👋 Event Recorder server stopped")
        sys.exit(0)


@cli.command()
@click.option(
    '--agents-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help='Path to directory containing agent Python files'
)
@click.option(
    '--events-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help='Path to directory containing event JSON files'
)
@click.option(
    '--recordings-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help='Path to directory containing event recording JSON files'
)
@click.option(
    '--event-flow-port',
    type=int,
    default=5555,
    help='Port for Event Flow service (default: 5555)'
)
@click.option(
    '--event-recorder-port',
    type=int,
    default=5556,
    help='Port for Event Recorder service (default: 5556)'
)
def serve_all(
    agents_dir: Path,
    events_dir: Path,
    recordings_dir: Path,
    event_flow_port: int,
    event_recorder_port: int
):
    """
    Launch all DevTools services simultaneously.

    Starts Event Flow (5555) and Event Recorder (5556) in parallel.
    Note: This requires running each service in a separate terminal or process.
    """
    import multiprocessing

    def run_event_flow():
        from ..config import EventFlowConfig
        config = EventFlowConfig(
            agents_dir=agents_dir,
            events_dir=events_dir,
            port=event_flow_port
        )
        server = EventFlowServer(config)
        server.run(host='0.0.0.0', debug=False)

    def run_event_recorder():
        from ..config import EventRecorderConfig
        config = EventRecorderConfig(
            recordings_dir=recordings_dir,
            port=event_recorder_port
        )
        server = EventRecorderServer(config)
        server.run(host='0.0.0.0', debug=False)

    click.echo("=" * 80)
    click.echo("🚀 Starting all PubSub DevTools services...")
    click.echo("=" * 80)
    click.echo(f"📊 Event Flow:     http://localhost:{event_flow_port}")
    click.echo(f"🎬 Event Recorder: http://localhost:{event_recorder_port}")
    click.echo()
    click.echo("Press Ctrl+C to stop all services")
    click.echo("=" * 80)
    click.echo()

    # Create processes for each service
    processes = []

    event_flow_process = multiprocessing.Process(target=run_event_flow)
    event_recorder_process = multiprocessing.Process(target=run_event_recorder)

    processes.append(event_flow_process)
    processes.append(event_recorder_process)

    try:
        # Start all processes
        for p in processes:
            p.start()

        # Wait for all processes
        for p in processes:
            p.join()

    except KeyboardInterrupt:
        click.echo("\n👋 Stopping all services...")
        for p in processes:
            if p.is_alive():
                p.terminate()
                p.join(timeout=5)
        click.echo("✅ All services stopped")
        sys.exit(0)


@cli.command()
def config_example():
    """
    Print an example configuration for DevTools services.

    Shows how to structure directories and configuration.
    """
    example = """
Example DevTools Configuration
================================

Directory Structure:
-------------------
project/
├── agents/              # Agent Python files
│   ├── market_agent.py
│   ├── risk_agent.py
│   └── execution_agent.py
├── events/              # Event JSON files
│   ├── MarketDataReceived.json
│   ├── RiskAssessed.json
│   └── OrderExecuted.json
└── recordings/          # Event recording sessions
    ├── session_2024-01-01.json
    └── session_2024-01-02.json

Launch Commands:
----------------
# Event Flow Visualization (port 5555)
pubsub-devtools event-flow \\
    --agents-dir ./agents \\
    --events-dir ./events \\
    --port 5555

# Event Recorder Dashboard (port 5556)
pubsub-devtools event-recorder \\
    --recordings-dir ./recordings \\
    --port 5556

# All services at once
pubsub-devtools serve-all \\
    --agents-dir ./agents \\
    --events-dir ./events \\
    --recordings-dir ./recordings \\
    --event-flow-port 5555 \\
    --event-recorder-port 5556

Configuration in Python:
------------------------
from pathlib import Path
from python_pubsub_devtools.config import DevToolsConfig

config = DevToolsConfig(
    agents_dir=Path("./agents"),
    events_dir=Path("./events"),
    recordings_dir=Path("./recordings"),
    event_flow_port=5555,
    event_recorder_port=5556
)

# Get service-specific configs
event_flow_config = config.get_event_flow_config()
event_recorder_config = config.get_event_recorder_config()
"""
    click.echo(example)


if __name__ == '__main__':
    cli()
