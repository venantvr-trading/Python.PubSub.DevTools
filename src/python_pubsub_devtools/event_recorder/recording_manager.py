"""
Gestion des sessions d'enregistrement d'événements.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class RecordingManager:
    """
    Gestionnaire centralisé des sessions d'enregistrement.

    Responsabilités:
    - Démarrage/arrêt de sessions d'enregistrement
    - Enregistrement d'événements
    - Sauvegarde des enregistrements
    """

    def __init__(self, recordings_dir: Path):
        self.recordings_dir = Path(recordings_dir)
        self._lock = threading.Lock()
        self._active = False
        self._session_name: Optional[str] = None
        self._start_time: Optional[datetime] = None
        self._events: List[Dict[str, Any]] = []

    def is_active(self) -> bool:
        """Vérifie si une session d'enregistrement est active."""
        with self._lock:
            return self._active

    def get_event_count(self) -> int:
        """Retourne le nombre d'événements dans la session active."""
        with self._lock:
            return len(self._events)

    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut de l'enregistrement.

        Returns:
            Dict avec {active, session_name, event_count}
        """
        with self._lock:
            return {
                'active': self._active,
                'session_name': self._session_name,
                'event_count': len(self._events)
            }

    def start_session(self, session_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Démarre une nouvelle session d'enregistrement.

        Args:
            session_name: Nom de la session (optionnel, auto-généré si absent)

        Returns:
            Dict avec {success, message, session_name}

        Raises:
            RuntimeError: Si une session est déjà active
        """
        with self._lock:
            if self._active:
                return {
                    'success': False,
                    'error': 'Recording already active'
                }

            if not session_name:
                session_name = f'session_{datetime.now().strftime("%Y%m%d_%H%M%S")}'

            self._active = True
            self._session_name = session_name
            self._start_time = datetime.now(timezone.utc)
            self._events = []

        print(f"🔴 Recording started: {session_name}")

        return {
            'success': True,
            'message': 'Recording started',
            'session_name': session_name
        }

    def record_event(
            self,
            event_name: str,
            event_data: Any,
            source: str,
            timestamp_offset_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enregistre un événement dans la session active.

        Args:
            event_name: Nom de l'événement
            event_data: Données de l'événement
            source: Source de l'événement
            timestamp_offset_ms: Offset temporel (calculé si absent)

        Returns:
            Dict avec {success, event_count}

        Raises:
            RuntimeError: Si aucune session n'est active
        """
        with self._lock:
            if not self._active:
                return {
                    'success': False,
                    'error': 'No active recording session'
                }

            # Calculer timestamp offset si non fourni
            if timestamp_offset_ms is None:
                timestamp_offset_ms = int(
                    (datetime.now(timezone.utc) - self._start_time).total_seconds() * 1000
                )

            # Ajouter l'événement
            self._events.append({
                'timestamp_offset_ms': timestamp_offset_ms,
                'event_name': event_name,
                'event_data': event_data,
                'source': source
            })

        return {
            'success': True,
            'event_count': len(self._events)
        }

    def stop_session(self) -> Dict[str, Any]:
        """
        Arrête l'enregistrement et sauvegarde dans un fichier.

        Returns:
            Dict avec {success, filename, event_count}

        Raises:
            RuntimeError: Si aucune session n'est active
        """
        with self._lock:
            if not self._active:
                return {
                    'success': False,
                    'error': 'No active recording session'
                }

            session_name = self._session_name
            events = self._events.copy()
            start_time = self._start_time

            # Créer le fichier d'enregistrement
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{session_name}_{timestamp}.json"
            filepath = self.recordings_dir / filename

            recording_data = {
                'session_name': session_name,
                'start_time': start_time.isoformat() if start_time else None,
                'duration_ms': events[-1]['timestamp_offset_ms'] if events else 0,
                'total_events': len(events),
                'events': events
            }

            with open(filepath, 'w') as f:
                json.dump(recording_data, f, indent=2)

            event_count = len(events)

            # Réinitialiser l'état
            self._active = False
            self._session_name = None
            self._start_time = None
            self._events = []

        print(f"✓ Recording saved: {filename} ({event_count} events)")

        return {
            'success': True,
            'message': 'Recording saved',
            'filename': filename,
            'event_count': event_count
        }
