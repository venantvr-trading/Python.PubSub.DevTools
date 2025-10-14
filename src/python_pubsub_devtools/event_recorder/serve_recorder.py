#!/usr/bin/env python3
"""
Event Recorder Dashboard

Web interface for viewing and replaying event recordings.

Usage:
    python tools/event_recorder/serve_recorder.py
"""
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from flask import Flask, render_template, jsonify

# Configure Flask to find templates and static files in parent tools directory
TOOLS_DIR = Path(__file__).parent.parent
app = Flask(__name__,
            template_folder=str(TOOLS_DIR / 'templates'),
            static_folder=str(TOOLS_DIR / 'static'))

# Paths
SCRIPT_DIR = Path(__file__).parent
RECORDINGS_DIR = SCRIPT_DIR / "recordings"
RECORDINGS_DIR.mkdir(exist_ok=True)

# Common UI colors - same as event_flow
GRADIENT_PRIMARY = '#667eea'
GRADIENT_SECONDARY = '#764ba2'


def load_recording(filename: str) -> Optional[Dict[str, Any]]:
    """Load a recording file"""
    file_path = RECORDINGS_DIR / filename
    if not file_path.exists():
        return None

    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading recording {filename}: {e}")
        return None


def get_recording_metadata(filename: str) -> Optional[Dict[str, Any]]:
    """Get metadata for a recording"""
    recording = load_recording(filename)
    if not recording:
        return None

    # Support both formats: with 'metadata' key or flat structure
    if 'metadata' in recording:
        metadata = recording['metadata']
        events = recording.get('events', [])
    else:
        # Flat structure - metadata is at root level
        metadata = recording
        events = recording.get('events', [])

    # Calculate duration
    if events:
        duration_ms = events[-1]['timestamp_offset_ms']
        duration_seconds = duration_ms / 1000
        if duration_seconds < 60:
            duration_str = f"{duration_seconds:.1f}s"
        else:
            minutes = int(duration_seconds // 60)
            seconds = int(duration_seconds % 60)
            duration_str = f"{minutes}m {seconds}s"
    else:
        duration_str = "0s"

    # Count unique event types
    unique_events = len(set(e['event_name'] for e in events))

    # Format created_at - try both 'created_at' and 'start_time'
    created_at = metadata.get('created_at') or metadata.get('start_time', 'Unknown')
    try:
        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        created_at_str = dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        created_at_str = created_at

    return {
        'filename': filename,
        'session_name': metadata.get('session_name', filename.replace('.json', '')),
        'created_at': created_at_str,
        'duration': duration_str,
        'event_count': len(events),
        'unique_events': unique_events,
    }


def get_all_recordings() -> List[Dict[str, Any]]:
    """Get metadata for all recordings"""
    recordings = []

    for file_path in RECORDINGS_DIR.glob('*.json'):
        metadata = get_recording_metadata(file_path.name)
        if metadata:
            recordings.append(metadata)

    # Sort by created_at descending
    recordings.sort(key=lambda x: x['created_at'], reverse=True)

    return recordings


@app.route('/')
def index():
    """Main page with recordings list"""
    recordings = get_all_recordings()

    # Calculate stats
    total_recordings = len(recordings)
    total_events = sum(r['event_count'] for r in recordings)

    # Calculate total duration
    total_duration_seconds = 0
    for recording_file in RECORDINGS_DIR.glob('*.json'):
        recording = load_recording(recording_file.name)
        if recording and recording.get('events'):
            duration_ms = recording['events'][-1]['timestamp_offset_ms']
            total_duration_seconds += duration_ms / 1000

    if total_duration_seconds < 60:
        total_duration = f"{total_duration_seconds:.0f}s"
    elif total_duration_seconds < 3600:
        minutes = int(total_duration_seconds // 60)
        total_duration = f"{minutes}m"
    else:
        hours = int(total_duration_seconds // 3600)
        minutes = int((total_duration_seconds % 3600) // 60)
        total_duration = f"{hours}h {minutes}m"

    avg_events = int(total_events / total_recordings) if total_recordings > 0 else 0

    return render_template(
        'event_recorder.html',
        recordings=recordings,
        total_recordings=total_recordings,
        total_events=total_events,
        total_duration=total_duration,
        avg_events_per_recording=avg_events
    )


@app.route('/recording/<filename>')
def recording_detail(filename: str):
    """Detail page for a specific recording"""
    recording_data = load_recording(filename)
    if not recording_data:
        return "Recording not found", 404

    metadata = get_recording_metadata(filename)
    events = recording_data.get('events', [])

    # Count events by type
    event_counts = Counter(e['event_name'] for e in events)
    max_count = max(event_counts.values()) if event_counts else 1

    # Sort by count descending
    event_counts = dict(sorted(event_counts.items(), key=lambda x: x[1], reverse=True))

    # Calculate events per second
    if events:
        duration_seconds = events[-1]['timestamp_offset_ms'] / 1000
        events_per_second = f"{len(events) / duration_seconds:.1f}" if duration_seconds > 0 else "N/A"
    else:
        events_per_second = "0"

    metadata['events_per_second'] = events_per_second

    return render_template(
        'recording_detail.html',
        recording=metadata,
        events=events[:500],  # Limit to first 500 for performance
        event_counts=event_counts,
        max_count=max_count
    )


@app.route('/api/recordings')
def api_recordings():
    """API endpoint for recordings list"""
    recordings = get_all_recordings()
    return jsonify(recordings)


@app.route('/api/recording/<filename>')
def api_recording(filename: str):
    """API endpoint for recording data"""
    recording = load_recording(filename)
    if not recording:
        return jsonify({'error': 'Recording not found'}), 404
    return jsonify(recording)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Event Recorder Dashboard")
    parser.add_argument("--port", type=int, default=5556, help="Port to run server on (default: 5556)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--recordings-dir", type=str, help="Path to recordings directory")
    args = parser.parse_args()

    # Update global recordings directory if provided
    global RECORDINGS_DIR
    if args.recordings_dir:
        RECORDINGS_DIR = Path(args.recordings_dir)
        RECORDINGS_DIR.mkdir(exist_ok=True)

    print("=" * 80)
    print("🎬 Event Recorder Dashboard")
    print("=" * 80)
    print()
    print(f"📁 Recordings directory: {RECORDINGS_DIR}")
    print(f"   Found {len(list(RECORDINGS_DIR.glob('*.json')))} recordings")
    print()
    print("🌐 Starting web server...")
    print()
    print(f"   📍 Open in browser: http://{args.host}:{args.port}")
    print()
    print("   Press Ctrl+C to stop")
    print("=" * 80)
    print()

    app.run(host=args.host, port=args.port, debug=True)


if __name__ == '__main__':
    main()
