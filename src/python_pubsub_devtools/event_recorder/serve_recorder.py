#!/usr/bin/env python3
"""
Event Recorder Dashboard Server

Launches a web server to browse and replay recorded event sessions.

Usage:
    python -m python_pubsub_devtools.event_recorder.serve_recorder
    pubsub-tools event-recorder
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .server import EventRecorderServer


def main():
    """
    Start the Event Recorder Dashboard server

    The server provides a web interface to browse recorded event sessions,
    view event timelines, and manage recordings.
    """
    parser = argparse.ArgumentParser(
        description="Event Recorder Dashboard Server"
    )
    parser.add_argument(
        "--recordings-dir",
        type=Path,
        default=Path("recordings"),
        help="Directory containing event recordings (default: recordings)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5556,
        help="Port to run server on (default: 5556)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    args = parser.parse_args()

    print("=" * 80)
    print("🎬 Event Recorder Dashboard")
    print("=" * 80)
    print()

    # Initialize config and server
    from ..config import EventRecorderConfig

    config = EventRecorderConfig(
        recordings_dir=args.recordings_dir,
        port=args.port
    )

    # Count recordings
    recordings_dir = config.recordings_dir
    recordings_dir.mkdir(parents=True, exist_ok=True)
    recording_count = len(list(recordings_dir.glob('*.json')))

    print(f"📁 Recordings directory: {recordings_dir}")
    print(f"   Found {recording_count} recordings")
    print()
    print("🌐 Starting web server...")
    print(f"   📍 Web UI: http://{args.host}:{args.port}")
    print(f"   📍 API: http://{args.host}:{args.port}/api")
    print()
    print("   Press Ctrl+C to stop")
    print("=" * 80)
    print()

    server = EventRecorderServer(config)
    server.run(host=args.host, debug=True)


if __name__ == '__main__':
    main()
