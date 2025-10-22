#!/usr/bin/env python3
"""
Mock Exchange Simulator Server

Launches a web server for market scenario simulation and candlestick replay.

Usage:
    python -m python_pubsub_devtools.mock_exchange.serve_exchange
    pubsub-tools mock-exchange
"""
from __future__ import annotations

import argparse
from pathlib import Path


def main():
    """
    Start the Mock Exchange Simulator server
    
    The server provides a web interface to upload replay files (CSV, JSON),
    manage market scenarios, and simulate exchange behavior.
    """
    parser = argparse.ArgumentParser(
        description="Mock Exchange Simulator Server"
    )
    parser.add_argument(
        "--replay-data-dir",
        type=Path,
        default=Path("replay_data"),
        help="Directory containing replay data files (default: replay_data)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5557,
        help="Port to run server on (default: 5557)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    args = parser.parse_args()

    print("=" * 80)
    print("🎰 Mock Exchange Simulator")
    print("=" * 80)
    print()

    # Initialize config and mock service bus
    from ..config import MockExchangeConfig
    from .server import MockExchangeServer

    config = MockExchangeConfig(
        replay_data_dir=args.replay_data_dir,
        port=args.port
    )

    print("🚌 Using PubSub client for candle publication")
    print(f"   PubSub URL: {config.pubsub_url}")
    print(f"   Candle topic: {config.candle_topic}")
    print()

    # Count replay files
    replay_data_dir = config.replay_data_dir
    replay_data_dir.mkdir(parents=True, exist_ok=True)
    replay_count = len(list(replay_data_dir.glob('*.csv')) + list(replay_data_dir.glob('*.json')))

    print(f"📂 Replay data directory: {replay_data_dir}")
    print(f"   Found {replay_count} replay file(s)")
    print()
    print("🌐 Starting web server...")
    print(f"   📍 Web UI: http://{args.host}:{args.port}")
    print(f"   📍 API: http://{args.host}:{args.port}/api")
    print()
    print("   Press Ctrl+C to stop")
    print("=" * 80)
    print()

    server = MockExchangeServer(config)
    server.run(host=args.host, debug=True)


if __name__ == '__main__':
    main()
