#!/usr/bin/env python3
"""
Event Recorder and Replayer - Time-Traveling Debugging

Record all events from a trading session and replay them later at any speed.
Perfect for debugging, testing, and reproducing issues.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Callable, Any


class EventRecorder:
    """Record all events to disk for later replay

    Usage:
        recorder = EventRecorder("bull_run_session")
        recorder.start_recording(service_bus)
        # ... bot runs ...
        recorder.save()
    """

    def __init__(self, session_name: str, output_dir: str = "recordings"):
        """Initialize recorder

        Args:
            session_name: Name of the recording session
            output_dir: Directory to save recordings (relative to tools/)
        """
        self.session_name = session_name
        self.output_dir = Path(__file__).parent / output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.events = []
        self.start_time = None
        self._original_publish = None
        self._service_bus = None

    def start_recording(self, service_bus) -> None:
        """Start intercepting and recording events

        Args:
            service_bus: The ServiceBus instance to record from
        """
        self.start_time = datetime.now(timezone.utc)
        self._service_bus = service_bus
        self._original_publish = service_bus.publish

        def recording_publish(event_name: str, event: Any, source: str):
            # Calculate timestamp offset from start
            timestamp_offset_ms = int(
                (datetime.now(timezone.utc) - self.start_time).total_seconds() * 1000
            )

            # Serialize event data
            try:
                if hasattr(event, 'model_dump'):
                    event_data = event.model_dump()
                elif hasattr(event, '__dict__'):
                    event_data = event.__dict__
                else:
                    event_data = str(event)
            except Exception as e:
                event_data = f"<serialization_error: {str(e)}>"

            # Record event
            self.events.append({
                "timestamp_offset_ms": timestamp_offset_ms,
                "event_name": event_name,
                "event_data": event_data,
                "source": source
            })

            # Call original publish
            return self._original_publish(event_name, event, source)

        service_bus.publish = recording_publish
        print(f"📼 Recording started: {self.session_name}")

    def stop_recording(self) -> None:
        """Stop recording and restore original publish method"""
        if self._service_bus and self._original_publish:
            self._service_bus.publish = self._original_publish
            print(f"⏸️  Recording stopped: {len(self.events)} events recorded")

    def save(self, filename: Optional[str] = None) -> Path:
        """Save recording to JSON file

        Args:
            filename: Optional custom filename (without extension)

        Returns:
            Path to saved recording file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.session_name}_{timestamp}.json"
        elif not filename.endswith('.json'):
            filename += '.json'

        filepath = self.output_dir / filename

        recording_data = {
            "session_name": self.session_name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "duration_ms": self.events[-1]["timestamp_offset_ms"] if self.events else 0,
            "total_events": len(self.events),
            "events": self.events
        }

        with open(filepath, 'w') as f:
            json.dump(recording_data, f, indent=2)

        print(f"💾 Recording saved: {filepath}")
        print(f"   - Total events: {len(self.events)}")
        print(f"   - Duration: {recording_data['duration_ms'] / 1000:.2f}s")

        return filepath

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.stop_recording()


class EventReplayer:
    """Replay recorded events at exact same timing or modified speed

    Usage:
        replayer = EventReplayer("recordings/session.json")
        replayer.replay(service_bus, speed_multiplier=10.0)  # 10x faster
    """

    def __init__(self, recording_file: str):
        """Initialize replayer

        Args:
            recording_file: Path to recording JSON file
        """
        recording_path = Path(recording_file)

        # Try relative to tools/ if not absolute
        if not recording_path.is_absolute():
            recording_path = Path(__file__).parent / recording_path

        if not recording_path.exists():
            raise FileNotFoundError(f"Recording not found: {recording_path}")

        with open(recording_path) as f:
            self.recording = json.load(f)

        self.events = self.recording["events"]
        self.session_name = self.recording["session_name"]
        self.duration_ms = self.recording["duration_ms"]

        print(f"📼 Recording loaded: {self.session_name}")
        print(f"   - Total events: {len(self.events)}")
        print(f"   - Duration: {self.duration_ms / 1000:.2f}s")

    def replay(
            self,
            service_bus,
            speed_multiplier: float = 1.0,
            event_filter: Optional[Callable[[str], bool]] = None,
            progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """Replay events with timing preservation

        Args:
            service_bus: ServiceBus instance to publish events to
            speed_multiplier: Speed control (1.0=real-time, 10.0=10x faster, 0.1=10x slower)
            event_filter: Optional function to filter events (return True to replay)
            progress_callback: Optional callback(current_event, total_events)
        """
        import importlib

        # Import events module dynamically
        try:
            events_module = importlib.import_module('python_pubsub_risk.events')
        except ImportError:
            print("⚠️  Warning: Could not import events module. Event reconstruction may fail.")
            events_module = None

        print(f"🎬 Replaying at {speed_multiplier}x speed...")

        last_timestamp = 0
        replayed_count = 0
        skipped_count = 0

        for i, event_data in enumerate(self.events):
            event_name = event_data["event_name"]

            # Apply filter if provided
            if event_filter and not event_filter(event_name):
                skipped_count += 1
                continue

            # Wait for correct timing
            timestamp = event_data["timestamp_offset_ms"]
            wait_time = (timestamp - last_timestamp) / 1000.0 / speed_multiplier

            if wait_time > 0:
                time.sleep(wait_time)

            # Reconstruct and publish event
            try:
                if events_module:
                    # Try to get event class from module
                    event_class = getattr(events_module, event_name, None)

                    if event_class and hasattr(event_class, 'model_validate'):
                        # Pydantic model - reconstruct from dict
                        event = event_class.model_validate(event_data["event_data"])
                    else:
                        # Fallback: use dict directly
                        event = event_data["event_data"]
                else:
                    # No events module - use dict
                    event = event_data["event_data"]

                # Publish event
                service_bus.publish(event_name, event, f"EventReplayer[{self.session_name}]")
                replayed_count += 1

            except Exception as e:
                print(f"⚠️  Failed to replay {event_name}: {e}")
                skipped_count += 1

            # Progress callback
            if progress_callback:
                progress_callback(i + 1, len(self.events))

            last_timestamp = timestamp

        print(f"✅ Replay complete!")
        print(f"   - Replayed: {replayed_count} events")
        if skipped_count > 0:
            print(f"   - Skipped: {skipped_count} events")

    def get_event_summary(self) -> dict:
        """Get summary statistics of recorded events

        Returns:
            Dictionary with event counts by type
        """
        from collections import Counter

        event_counts = Counter(e["event_name"] for e in self.events)
        return dict(event_counts.most_common())

    def filter_events(self, event_filter: Callable[[str], bool]) -> 'EventReplayer':
        """Create a new replayer with filtered events

        Args:
            event_filter: Function that returns True for events to keep

        Returns:
            New EventReplayer with filtered events
        """
        filtered_events = [e for e in self.events if event_filter(e["event_name"])]

        # Create new recording dict
        filtered_recording = {
            "session_name": f"{self.session_name}_filtered",
            "start_time": self.recording["start_time"],
            "duration_ms": filtered_events[-1]["timestamp_offset_ms"] if filtered_events else 0,
            "total_events": len(filtered_events),
            "events": filtered_events
        }

        # Create new replayer instance
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(filtered_recording, f)
            temp_path = f.name

        return EventReplayer(temp_path)

    def print_timeline(self, max_events: int = 50) -> None:
        """Print a timeline of events to console

        Args:
            max_events: Maximum number of events to display
        """
        print(f"\n📊 Event Timeline: {self.session_name}")
        print("=" * 80)

        events_to_show = self.events[:max_events]

        for event_data in events_to_show:
            timestamp_sec = event_data["timestamp_offset_ms"] / 1000.0
            event_name = event_data["event_name"]
            source = event_data["source"]

            # Color code by event type
            if "Failed" in event_name:
                marker = "❌"
            elif "Purchased" in event_name or "Sold" in event_name:
                marker = "💰"
            elif "Started" in event_name or "Completed" in event_name:
                marker = "🔄"
            else:
                marker = "📨"

            print(f"{timestamp_sec:7.2f}s {marker} {event_name:40s} <- {source}")

        if len(self.events) > max_events:
            print(f"\n... and {len(self.events) - max_events} more events")

        print("=" * 80)


def main():
    """CLI interface for event recorder/replayer"""
    import argparse

    parser = argparse.ArgumentParser(description="Event Recorder/Replayer CLI")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Replay command
    replay_parser = subparsers.add_parser('replay', help='Replay a recording')
    replay_parser.add_argument('recording', help='Recording file to replay')
    replay_parser.add_argument('--speed', type=float, default=1.0, help='Speed multiplier')
    replay_parser.add_argument('--filter', help='Filter events (e.g., "Failed" to only replay failed events)')

    # Info command
    info_parser = subparsers.add_parser('info', help='Show recording info')
    info_parser.add_argument('recording', help='Recording file')

    # Timeline command
    timeline_parser = subparsers.add_parser('timeline', help='Show event timeline')
    timeline_parser.add_argument('recording', help='Recording file')
    timeline_parser.add_argument('--max-events', type=int, default=50, help='Max events to show')

    args = parser.parse_args()

    if args.command == 'info':
        replayer = EventReplayer(args.recording)
        print("\n📊 Event Summary:")
        for event_name, count in replayer.get_event_summary().items():
            print(f"  {event_name:50s} {count:4d}x")

    elif args.command == 'timeline':
        replayer = EventReplayer(args.recording)
        replayer.print_timeline(max_events=args.max_events)

    elif args.command == 'replay':
        print("⚠️  Replay requires an active ServiceBus instance.")
        print("    Use this from Python code, not CLI.")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
