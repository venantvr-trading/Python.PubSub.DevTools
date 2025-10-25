"""
Scenario Testing Standalone Server - Entry point for scenario testing server.

Launches a standalone web server to execute test scenarios with chaos
engineering and declarative assertions.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

from .server import ScenarioTestingServer
from ..config import ScenarioTestingConfig

logger = logging.getLogger(__name__)


class MockServiceBus:
    """
    Mock ServiceBus for standalone testing.

    Simulates a service bus without external dependencies. All published
    events are recorded and logged to the console.

    Attributes:
        published_events: List of all published events
    """

    def __init__(self):
        """Initialize the MockServiceBus"""
        self.published_events: list[dict[str, Any]] = []
        self._pubsub_client = None  # Mock n'a pas de vraie connexion PubSub

    def publish(self, event_name: str, event: Any, source: str) -> None:
        """
        Publish an event (mock).

        Args:
            event_name: Name of the event
            event: Event data
            source: Event source
        """
        event_record = {
            'event_name': event_name,
            'event': event,
            'source': source
        }
        self.published_events.append(event_record)
        logger.debug(f"[MOCK BUS] {source} -> {event_name}: {event}")

    def clear_history(self) -> None:
        """Clear published events history"""
        self.published_events.clear()

    def get_events(self, event_name: str | None = None) -> list[dict[str, Any]]:
        """
        Get published events.

        Args:
            event_name: Optional - filter by event name

        Returns:
            List of events (filtered if event_name specified)
        """
        if event_name is None:
            return self.published_events.copy()
        return [e for e in self.published_events if e['event_name'] == event_name]


def main():
    """
    Main entry point for the Scenario Testing server.

    Launches the Flask server with a MockServiceBus for standalone testing.
    """
    parser = argparse.ArgumentParser(
        description="Scenario Testing Dashboard Server - Test with Chaos Engineering"
    )
    parser.add_argument(
        '--scenarios-dir',
        type=Path,
        default=Path('scenarios'),
        help='Directory containing scenario YAML files (default: scenarios)'
    )
    parser.add_argument(
        '--reports-dir',
        type=Path,
        default=Path('test_reports'),
        help='Directory for test reports (default: test_reports)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5558,
        help='Port to run server on (default: 5558)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host to bind server to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run Flask in debug mode (not recommended with threads)'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create configuration
    config = ScenarioTestingConfig(
        scenarios_dir=args.scenarios_dir,
        reports_dir=args.reports_dir,
        port=args.port
    )

    # Create mock service bus for standalone operation
    service_bus = MockServiceBus()
    logger.info("Using MockServiceBus for standalone operation")

    # Create and run server
    server = ScenarioTestingServer(config, service_bus)

    try:
        server.run(host=args.host, debug=args.debug)
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        logger.info("Server stopped by user")


if __name__ == '__main__':
    main()
