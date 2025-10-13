"""
Event Recorder Dashboard Server

Web interface for viewing and replaying event recordings.
"""
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from flask import Flask, render_template, jsonify

from ..config import EventRecorderConfig


class EventRecorderServer:
    """Flask server for event recorder dashboard"""

    def __init__(self, config: EventRecorderConfig):
        self.config = config
        self.app = self._create_app()

    def _create_app(self) -> Flask:
        package_root = Path(__file__).parent.parent
        app = Flask(__name__,
                    template_folder=str(package_root / 'web' / 'templates'),
                    static_folder=str(package_root / 'web' / 'static'))

        @app.route('/')
        def index():
            return self._index()

        @app.route('/recording/<filename>')
        def recording_detail(filename: str):
            return self._recording_detail(filename)

        @app.route('/api/recordings')
        def api_recordings():
            return jsonify(self._get_all_recordings())

        @app.route('/api/recording/<filename>')
        def api_recording(filename: str):
            recording = self._load_recording(filename)
            if not recording:
                return jsonify({'error': 'Recording not found'}), 404
            return jsonify(recording)

        return app

    def _load_recording(self, filename: str) -> Optional[Dict[str, Any]]:
        file_path = self.config.recordings_dir / filename
        if not file_path.exists():
            return None
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading recording {filename}: {e}")
            return None

    def _get_recording_metadata(self, filename: str) -> Optional[Dict[str, Any]]:
        recording = self._load_recording(filename)
        if not recording:
            return None

        if 'metadata' in recording:
            metadata = recording['metadata']
            events = recording.get('events', [])
        else:
            metadata = recording
            events = recording.get('events', [])

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

        unique_events = len(set(e['event_name'] for e in events))

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

    def _get_all_recordings(self) -> List[Dict[str, Any]]:
        recordings = []
        for file_path in self.config.recordings_dir.glob('*.json'):
            metadata = self._get_recording_metadata(file_path.name)
            if metadata:
                recordings.append(metadata)
        recordings.sort(key=lambda x: x['created_at'], reverse=True)
        return recordings

    def _index(self):
        recordings = self._get_all_recordings()
        total_recordings = len(recordings)
        total_events = sum(r['event_count'] for r in recordings)

        total_duration_seconds = 0
        for recording_file in self.config.recordings_dir.glob('*.json'):
            recording = self._load_recording(recording_file.name)
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

    def _recording_detail(self, filename: str):
        recording_data = self._load_recording(filename)
        if not recording_data:
            return "Recording not found", 404

        metadata = self._get_recording_metadata(filename)
        events = recording_data.get('events', [])

        event_counts = Counter(e['event_name'] for e in events)
        max_count = max(event_counts.values()) if event_counts else 1
        event_counts = dict(sorted(event_counts.items(), key=lambda x: x[1], reverse=True))

        if events:
            duration_seconds = events[-1]['timestamp_offset_ms'] / 1000
            events_per_second = f"{len(events) / duration_seconds:.1f}" if duration_seconds > 0 else "N/A"
        else:
            events_per_second = "0"

        metadata['events_per_second'] = events_per_second

        return render_template(
            'recording_detail.html',
            recording=metadata,
            events=events[:500],
            event_counts=event_counts,
            max_count=max_count
        )

    def run(self, host: str = '0.0.0.0', debug: bool = True):
        print("=" * 80)
        print("🎬 Event Recorder Dashboard")
        print("=" * 80)
        print(f"📁 Recordings directory: {self.config.recordings_dir}")
        print(f"   Found {len(list(self.config.recordings_dir.glob('*.json')))} recordings")
        print()
        print("🌐 Starting web server...")
        print(f"   📍 Open in browser: http://localhost:{self.config.port}")
        print("   Press Ctrl+C to stop")
        print("=" * 80)
        print()

        self.app.run(host=host, port=self.config.port, debug=debug)
        return 0
