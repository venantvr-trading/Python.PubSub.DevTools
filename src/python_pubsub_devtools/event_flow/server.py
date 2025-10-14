"""
Event Flow Server - Wrapper for serve_event_flow Flask app
"""
from pathlib import Path

from .serve_event_flow import app


class EventFlowServer:
    """Server for Event Flow Visualization"""

    def __init__(self, config):
        """Initialize server with configuration

        Args:
            config: EventFlowConfig object with agents_dir, events_dir, and port
        """
        self.config = config
        self.agents_dir = config.agents_dir
        self.events_dir = config.events_dir
        self.port = config.port

        # Update global paths in serve_event_flow
        import python_pubsub_devtools.event_flow.serve_event_flow as serve_module
        serve_module.AGENTS_DIR = Path(self.agents_dir)
        serve_module.EVENTS_DIR = Path(self.events_dir)

    def run(self, host='0.0.0.0', debug=True):
        """Run the Flask server

        Args:
            host: Host to bind to (default: 0.0.0.0)
            debug: Enable debug mode (default: True)
        """
        print("=" * 80)
        print("🚀 Event Flow Visualization Server")
        print("=" * 80)
        print()
        print(f"📊 Agents directory: {self.agents_dir}")
        print(f"📝 Events directory: {self.events_dir}")
        print()
        print(f"🌐 Server running at: http://{host}:{self.port}")
        print()
        print("   Press Ctrl+C to stop")
        print("=" * 80)
        print()

        app.run(host=host, port=self.port, debug=debug)