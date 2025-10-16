"""
Routes Flask pour le tableau de bord Event Recorder.
"""
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from flask import Flask, render_template, jsonify, current_app


def load_recording(filename: str) -> Optional[Dict[str, Any]]:
    """Charge un fichier d'enregistrement.

    Args:
        filename: Nom du fichier JSON à charger

    Returns:
        Données de l'enregistrement ou None si erreur
    """
    recordings_dir = Path(current_app.config['RECORDINGS_DIR'])
    file_path = recordings_dir / filename

    if not file_path.exists():
        return None

    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading recording {filename}: {e}")
        return None


def get_recording_metadata(filename: str) -> Optional[Dict[str, Any]]:
    """Extrait les métadonnées d'un enregistrement.

    Args:
        filename: Nom du fichier d'enregistrement

    Returns:
        Dictionnaire de métadonnées ou None si erreur
    """
    recording = load_recording(filename)
    if not recording:
        return None

    # Support des deux formats: avec clé 'metadata' ou structure plate
    if 'metadata' in recording:
        metadata = recording['metadata']
        events = recording.get('events', [])
    else:
        # Structure plate - métadonnées au niveau racine
        metadata = recording
        events = recording.get('events', [])

    # Calculer la durée
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

    # Compter les types d'événements uniques
    unique_events = len(set(e['event_name'] for e in events))

    # Formater created_at - essayer 'created_at' et 'start_time'
    created_at = metadata.get('created_at') or metadata.get('start_time', 'Unknown')
    try:
        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        created_at_str = dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
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
    """Liste tous les enregistrements disponibles.

    Returns:
        Liste des métadonnées de tous les enregistrements
    """
    recordings = []
    recordings_dir = Path(current_app.config['RECORDINGS_DIR'])

    for file_path in recordings_dir.glob('*.json'):
        metadata = get_recording_metadata(file_path.name)
        if metadata:
            recordings.append(metadata)

    # Trier par created_at décroissant
    recordings.sort(key=lambda x: x['created_at'], reverse=True)

    return recordings


def register_routes(app: Flask) -> None:
    """Enregistre toutes les routes Flask dans l'application.

    Args:
        app: Instance Flask
    """

    @app.route('/')
    def index():
        """Page principale avec la liste des enregistrements."""
        recordings = get_all_recordings()

        # Calculer les statistiques
        total_recordings = len(recordings)
        total_events = sum(r['event_count'] for r in recordings)

        # Calculer la durée totale
        total_duration_seconds = 0
        recordings_dir = Path(current_app.config['RECORDINGS_DIR'])

        for recording_file in recordings_dir.glob('*.json'):
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
        """Page de détail pour un enregistrement spécifique."""
        recording_data = load_recording(filename)
        if not recording_data:
            return "Recording not found", 404

        metadata = get_recording_metadata(filename)
        events = recording_data.get('events', [])

        # Compter les événements par type
        event_counts = Counter(e['event_name'] for e in events)
        max_count = max(event_counts.values()) if event_counts else 1

        # Trier par nombre décroissant
        event_counts = dict(sorted(event_counts.items(), key=lambda x: x[1], reverse=True))

        # Calculer les événements par seconde
        if events:
            duration_seconds = events[-1]['timestamp_offset_ms'] / 1000
            events_per_second = f"{len(events) / duration_seconds:.1f}" if duration_seconds > 0 else "N/A"
        else:
            events_per_second = "0"

        metadata['events_per_second'] = events_per_second

        return render_template(
            'recording_detail.html',
            recording=metadata,
            events=events[:500],  # Limiter à 500 pour les performances
            event_counts=event_counts,
            max_count=max_count
        )

    @app.route('/api/recordings')
    def api_recordings():
        """Endpoint API pour la liste des enregistrements."""
        recordings = get_all_recordings()
        return jsonify(recordings)

    @app.route('/api/recording/<filename>')
    def api_recording(filename: str):
        """Endpoint API pour les données d'un enregistrement."""
        recording = load_recording(filename)
        if not recording:
            return jsonify({'error': 'Recording not found'}), 404
        return jsonify(recording)
