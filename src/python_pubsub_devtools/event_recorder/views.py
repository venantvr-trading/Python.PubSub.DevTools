"""
Routes Flask pour le tableau de bord Event Recorder.
"""
from __future__ import annotations

import json
import threading
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from flask import Flask, render_template, jsonify, current_app

from .player_manager import PlayerManager
from .recording_manager import RecordingManager

# Managers globaux
player_manager: Optional[PlayerManager] = None
recording_manager: Optional[RecordingManager] = None
event_listener = None  # EventListener initialisé dans register_routes

# État global du replay
replay_state: Dict[str, Any] = {
    'active': False,
    'filename': None,
    'current_event_index': 0,
    'total_events': 0,
    'speed': 1.0,
    'paused': False,
    'simulation_mode': True,
    'events': [],
    'replayer': None,
    'replay_thread': None
}
replay_lock = threading.Lock()

# Managers dédiés (nouvelle architecture)
player_manager: Optional[PlayerManager] = None
recording_manager: Optional[RecordingManager] = None


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
    global player_manager, recording_manager, event_listener

    # Initialiser les managers
    recordings_dir = Path(app.config['RECORDINGS_DIR'])
    pubsub_url = app.config.get('PUBSUB_URL', 'http://localhost:5000')
    player_manager = PlayerManager(pubsub_url=pubsub_url)
    recording_manager = RecordingManager(recordings_dir)

    # Initialiser le listener d'événements (ne démarre pas automatiquement)
    from .event_listener import EventListener
    event_listener = EventListener(pubsub_url, recording_manager)

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
            title='🎬 Event Recorder Dashboard',
            subtitle='View and replay event recordings',
            active_page='recorder',
            footer_text='🎬 Event Recorder Dashboard | Port 5556 | <kbd>Ctrl+R</kbd> to refresh',
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
            events=events,  # Charger tous les événements
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

    @app.route('/api/recording/<filename>/events')
    def api_recording_events(filename: str):
        """Récupère tous les événements d'un enregistrement avec détails complets.

        Query params:
            event_name: Filtrer par nom d'événement
            source: Filtrer par source
            limit: Nombre maximum d'événements (défaut: tous)
            offset: Offset pour pagination (défaut: 0)
        """
        from flask import request

        recording = load_recording(filename)
        if not recording:
            return jsonify({'error': 'Recording not found'}), 404

        events = recording.get('events', [])

        # Filtrage par nom d'événement
        event_name_filter = request.args.get('event_name')
        if event_name_filter:
            events = [e for e in events if e['event_name'] == event_name_filter]

        # Filtrage par source
        source_filter = request.args.get('source')
        if source_filter:
            events = [e for e in events if e.get('source') == source_filter]

        # Pagination
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int, default=0)

        total_events = len(events)

        if limit:
            events = events[offset:offset + limit]
        else:
            events = events[offset:]

        return jsonify({
            'filename': filename,
            'total_events': total_events,
            'returned_events': len(events),
            'offset': offset,
            'events': events
        })

    @app.route('/api/recording/<filename>/fields')
    def api_recording_fields(filename: str):
        """Récupère les champs disponibles dans les événements pour le filtrage."""
        recording = load_recording(filename)
        if not recording:
            return jsonify({'error': 'Recording not found'}), 404

        events = recording.get('events', [])
        if not events:
            return jsonify({'fields': []})

        # Collecter tous les champs uniques des event_data
        all_fields = set()
        event_types = set()
        sources = set()

        for event in events:
            event_types.add(event['event_name'])
            sources.add(event.get('source', 'Unknown'))

            # Analyser les champs dans event_data
            event_data = event.get('event_data', {})
            if isinstance(event_data, dict):
                all_fields.update(event_data.keys())

        return jsonify({
            'event_types': sorted(list(event_types)),
            'sources': sorted(list(sources)),
            'data_fields': sorted(list(all_fields))
        })

    @app.route('/api/recording/create', methods=['POST'])
    def api_create_recording():
        """Crée un nouveau fichier d'enregistrement à partir d'événements sélectionnés.

        Request JSON:
            source_filename: Fichier source
            event_indices: Liste des indices d'événements à inclure
            new_session_name: Nom de la nouvelle session
        """
        from flask import request

        data = request.json
        source_filename = data.get('source_filename')
        event_indices = data.get('event_indices', [])
        new_session_name = data.get('new_session_name', 'filtered_session')

        if not source_filename:
            return jsonify({'error': 'source_filename is required'}), 400

        # Charger l'enregistrement source
        recording = load_recording(source_filename)
        if not recording:
            return jsonify({'error': 'Source recording not found'}), 404

        source_events = recording.get('events', [])

        # Sélectionner les événements
        if not event_indices:
            # Si aucun indice, prendre tous les événements
            selected_events = source_events
        else:
            selected_events = [source_events[i] for i in event_indices if i < len(source_events)]

        if not selected_events:
            return jsonify({'error': 'No events selected'}), 400

        # Recalculer les timestamps (offset depuis 0)
        first_timestamp = selected_events[0]['timestamp_offset_ms']
        for event in selected_events:
            event['timestamp_offset_ms'] -= first_timestamp

        # Créer le nouveau fichier
        recordings_dir = Path(current_app.config['RECORDINGS_DIR'])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{new_session_name}_{timestamp}.json"
        new_filepath = recordings_dir / new_filename

        new_recording = {
            'session_name': new_session_name,
            'start_time': datetime.now().isoformat(),
            'duration_ms': selected_events[-1]['timestamp_offset_ms'] if selected_events else 0,
            'total_events': len(selected_events),
            'source_file': source_filename,
            'events': selected_events
        }

        with open(new_filepath, 'w') as f:
            json.dump(new_recording, f, indent=2)

        return jsonify({
            'success': True,
            'filename': new_filename,
            'event_count': len(selected_events)
        })

    @app.route('/api/replay/start/<filename>', methods=['POST'])
    def api_replay_start(filename: str):
        """Démarre le replay d'un enregistrement.

        Request JSON:
            speed: Vitesse de replay (0.1 à 10.0, défaut 1.0)
            simulation_mode: Si True, ne publie pas sur PubSub (défaut False)
        """
        global replay_state
        from flask import request

        recording = load_recording(filename)
        if not recording:
            return jsonify({'error': 'Recording not found'}), 404

        data = request.json or {}
        speed = data.get('speed', 1.0)
        simulation_mode = data.get('simulation_mode', False)
        events = recording.get('events', [])

        with replay_lock:
            if replay_state['active']:
                return jsonify({
                    'error': 'Replay already active',
                    'active_file': replay_state.get('filename', 'unknown')
                }), 409  # 409 Conflict

            replay_state['active'] = True
            replay_state['filename'] = filename
            replay_state['current_event_index'] = 0
            replay_state['total_events'] = len(events)
            replay_state['speed'] = speed
            replay_state['paused'] = False
            replay_state['simulation_mode'] = simulation_mode
            replay_state['events'] = events

        if not simulation_mode:
            # Vrai replay via PubSub
            def progress_callback(current: int, total: int):
                """Mise à jour de la progression du replay"""
                with replay_lock:
                    replay_state['current_event_index'] = current

            def replay_thread_fn():
                try:
                    player_manager.replay_events(
                        events,
                        speed,
                        None,
                        progress_callback=progress_callback
                    )
                except Exception as e:
                    print(f"❌ Replay error: {e}")
                finally:
                    with replay_lock:
                        replay_state['active'] = False

            thread = threading.Thread(target=replay_thread_fn, daemon=True)
            thread.start()
            replay_state['replay_thread'] = thread
            message = 'Replay started (publishing to PubSub)'
        else:
            # Mode simulation pour l'UI uniquement
            message = 'Replay started (simulation mode - no actual publishing)'

        return jsonify({
            'success': True,
            'message': message,
            'total_events': len(events),
            'simulation_mode': simulation_mode
        })

    @app.route('/api/replay/pause', methods=['POST'])
    def api_replay_pause():
        """Met en pause le replay."""
        global replay_state

        with replay_lock:
            if not replay_state['active']:
                return jsonify({'error': 'No active replay'}), 400

            replay_state['paused'] = not replay_state['paused']
            status = 'paused' if replay_state['paused'] else 'playing'

            # Informer le PlayerManager si ce n'est pas en mode simulation
            if not replay_state['simulation_mode']:
                player_manager.pause_replay(replay_state['paused'])

        return jsonify({'success': True, 'status': status})

    @app.route('/api/replay/stop', methods=['POST'])
    def api_replay_stop():
        """Arrête le replay."""
        global replay_state

        with replay_lock:
            # Informer le PlayerManager si ce n'est pas en mode simulation
            if not replay_state['simulation_mode']:
                player_manager.stop_replay()

            replay_state['active'] = False
            replay_state['paused'] = False
            replay_state['current_event_index'] = 0

        return jsonify({'success': True, 'message': 'Replay stopped'})

    @app.route('/api/replay/speed', methods=['POST'])
    def api_replay_speed():
        """Change la vitesse de replay.

        Request JSON:
            speed: Nouvelle vitesse (0.1 à 10.0)
        """
        global replay_state
        from flask import request

        data = request.json or {}
        speed = data.get('speed', 1.0)

        with replay_lock:
            # Permettre le changement de vitesse même si pas actif (préréglage)
            replay_state['speed'] = speed

        return jsonify({'success': True, 'speed': speed})

    @app.route('/api/replay/status')
    def api_replay_status():
        """Récupère le statut du replay."""
        global replay_state

        with replay_lock:
            # Simuler l'avancement UNIQUEMENT en mode simulation
            if replay_state['simulation_mode'] and replay_state['active'] and not replay_state['paused']:
                replay_state['current_event_index'] += 1
                if replay_state['current_event_index'] >= replay_state['total_events']:
                    replay_state['active'] = False
                    replay_state['current_event_index'] = replay_state['total_events']

            status = {
                'active': replay_state['active'],
                'paused': replay_state['paused'],
                'current_event': replay_state['current_event_index'],
                'total_events': replay_state['total_events'],
                'speed': replay_state['speed'],
                'simulation_mode': replay_state['simulation_mode'],
                'filename': replay_state.get('filename', ''),
                'progress': (replay_state['current_event_index'] / replay_state['total_events'] * 100) if replay_state['total_events'] > 0 else 0
            }

        return jsonify(status)

    # ========== API d'enregistrement (Recording) ==========

    @app.route('/api/record/start', methods=['POST'])
    def api_record_start():
        """Démarre une nouvelle session d'enregistrement.

        Request JSON:
            session_name: Nom de la session (optionnel, défaut: auto-généré)
        """
        from flask import request

        data = request.json or {}
        session_name = data.get('session_name')

        result = recording_manager.start_session(session_name)

        if result['success']:
            # Démarrer le listener PubSub pour écouter tous les événements
            if event_listener and not event_listener.is_running():
                if event_listener.start():
                    result['listener_status'] = 'started'
                else:
                    result['listener_status'] = 'failed_to_start'
            else:
                result['listener_status'] = 'already_running'

            return jsonify(result)
        else:
            return jsonify({'error': result.get('error')}), 400

    @app.route('/api/record/event', methods=['POST'])
    def api_record_event():
        """Enregistre un événement dans la session active.

        Request JSON:
            event_name: Nom de l'événement
            event_data: Données de l'événement (dict)
            source: Source de l'événement
            timestamp_offset_ms: Offset temporel (optionnel, calculé si absent)
        """
        from flask import request

        data = request.json
        if not data or 'event_name' not in data:
            return jsonify({'error': 'event_name is required'}), 400

        event_name = data['event_name']
        event_data = data.get('event_data', {})
        source = data.get('source', 'Unknown')
        timestamp_offset_ms = data.get('timestamp_offset_ms')

        result = recording_manager.record_event(
            event_name, event_data, source, timestamp_offset_ms
        )

        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result.get('error')}), 400

    @app.route('/api/record/stop', methods=['POST'])
    def api_record_stop():
        """Arrête l'enregistrement et sauvegarde dans un fichier."""
        result = recording_manager.stop_session()

        if result['success']:
            # Arrêter le listener PubSub
            if event_listener and event_listener.is_running():
                event_listener.stop()
                result['listener_status'] = 'stopped'
            else:
                result['listener_status'] = 'not_running'

            return jsonify(result)
        else:
            return jsonify({'error': result.get('error')}), 400

    @app.route('/api/record/status')
    def api_record_status():
        """Récupère le statut de l'enregistrement."""
        return jsonify(recording_manager.get_status())

    @app.route('/api/pubsub/status')
    def api_pubsub_status():
        """Récupère le statut de connexion PubSub."""
        connected = player_manager._pubsub_client is not None if player_manager else False
        return jsonify({'connected': connected})
