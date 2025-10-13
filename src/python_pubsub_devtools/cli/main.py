"""
PubSub Dev Tools CLI

Command-line interface for launching dev tools.
"""
import argparse
import sys
from pathlib import Path

from ..config import DevToolsConfig


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog='pubsub-tools',
        description='PubSub Dev Tools - Development tools for PubSub architectures',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  pubsub-tools event-flow --config devtools_config.yaml
  pubsub-tools event-recorder
  pubsub-tools mock-exchange
  pubsub-tools dashboard  # Launch all tools
        '''
    )

    parser.add_argument(
        '--config', '-c',
        default='devtools_config.yaml',
        help='Path to configuration file (default: devtools_config.yaml)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Event Flow command
    event_flow_parser = subparsers.add_parser(
        'event-flow',
        help='Launch event flow visualizer'
    )
    event_flow_parser.add_argument(
        '--port', '-p',
        type=int,
        help='Port to run server on (overrides config)'
    )

    # Event Recorder command
    recorder_parser = subparsers.add_parser(
        'event-recorder',
        help='Launch event recorder dashboard'
    )
    recorder_parser.add_argument(
        '--port', '-p',
        type=int,
        help='Port to run server on (overrides config)'
    )

    # Mock Exchange command
    exchange_parser = subparsers.add_parser(
        'mock-exchange',
        help='Launch mock exchange simulator'
    )
    exchange_parser.add_argument(
        '--port', '-p',
        type=int,
        help='Port to run server on (overrides config)'
    )

    # Dashboard command (all services)
    dashboard_parser = subparsers.add_parser(
        'dashboard',
        help='Launch all dashboards (event-flow, event-recorder, mock-exchange)'
    )

    # Metrics command
    from .commands import setup_metrics_parser

    setup_metrics_parser(subparsers)

    # Version command
    version_parser = subparsers.add_parser(
        'version',
        help='Show version information'
    )

    args = parser.parse_args()

    # Show help if no command provided
    if not args.command:
        parser.print_help()
        return 0

    # Handle version command
    if args.command == 'version':
        from .. import __version__

        print(f"PubSub Dev Tools version {__version__}")
        return 0

    # Handle metrics command
    if args.command == 'metrics':
        # Metrics commands don't require config file
        if hasattr(args, 'func'):
            return args.func(args)
        else:
            print("❌ Error: No metrics subcommand specified")
            print("Use: pubsub-tools metrics --help")
            return 1

    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Error: Config file not found: {config_path}")
        print(f"\nCreate a config file using:")
        print(f"  cp examples/config.example.yaml {args.config}")
        return 1

    try:
        config = DevToolsConfig.from_yaml(config_path)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return 1

    # Execute command
    if args.command == 'event-flow':
        from ..event_flow.server import EventFlowServer

        if args.port:
            config.event_flow.port = args.port

        server = EventFlowServer(config.event_flow)
        return server.run()

    elif args.command == 'event-recorder':
        from ..event_recorder.server import EventRecorderServer

        if args.port:
            config.event_recorder.port = args.port

        server = EventRecorderServer(config.event_recorder)
        return server.run()

    elif args.command == 'mock-exchange':
        from ..mock_exchange.server import MockExchangeServer

        if args.port:
            config.mock_exchange.port = args.port

        server = MockExchangeServer(config.mock_exchange)
        return server.run()

    elif args.command == 'dashboard':
        print("🚀 Launching all dashboards...")
        print()
        print("This will start all services:")
        print(f"  • Event Flow:        http://localhost:{config.event_flow.port}")
        print(f"  • Event Recorder:    http://localhost:{config.event_recorder.port}")
        print(f"  • Mock Exchange:     http://localhost:{config.mock_exchange.port}")
        print()
        print("⚠️  Note: Running all services simultaneously requires multiple terminals.")
        print("   Consider using tmux or screen for better management.")
        print()
        print("To launch individually:")
        print(f"  pubsub-tools event-flow --config {args.config}")
        print(f"  pubsub-tools event-recorder --config {args.config}")
        print(f"  pubsub-tools mock-exchange --config {args.config}")
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
