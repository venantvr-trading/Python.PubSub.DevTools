"""
Gestion des players enregistrés pour le replay d'événements.
"""
from __future__ import annotations

import threading
import time
from typing import Dict, List, Optional

import requests


class PlayerManager:
    """
    Gestionnaire centralisé des players enregistrés.

    Responsabilités:
    - Enregistrement/désenregistrement des players
    - Liste des players actifs
    - Envoi d'événements aux players (replay)
    """

    def __init__(self):
        self._players: Dict[str, str] = {}  # consumer_name -> player_endpoint
        self._lock = threading.Lock()

    def register(self, consumer_name: str, player_endpoint: str) -> bool:
        """
        Enregistre un player endpoint.

        Args:
            consumer_name: Nom du consumer
            player_endpoint: URL du endpoint player

        Returns:
            True si enregistré avec succès
        """
        with self._lock:
            self._players[consumer_name] = player_endpoint
        print(f"✓ Player registered: {consumer_name} -> {player_endpoint}")
        return True

    def unregister(self, player_endpoint: str) -> Optional[str]:
        """
        Désenregistre un player par son endpoint.

        Args:
            player_endpoint: URL du endpoint player

        Returns:
            Nom du consumer si trouvé, None sinon
        """
        with self._lock:
            for name, endpoint in list(self._players.items()):
                if endpoint == player_endpoint:
                    del self._players[name]
                    print(f"✓ Player unregistered: {name}")
                    return name
        return None

    def get_all(self) -> List[Dict[str, str]]:
        """
        Liste tous les players enregistrés.

        Returns:
            Liste de dicts {consumer_name, player_endpoint}
        """
        with self._lock:
            return [
                {'consumer_name': name, 'player_endpoint': endpoint}
                for name, endpoint in self._players.items()
            ]

    def count(self) -> int:
        """Retourne le nombre de players enregistrés."""
        with self._lock:
            return len(self._players)

    def has_players(self) -> bool:
        """Vérifie s'il y a des players enregistrés."""
        return self.count() > 0

    def get_players_copy(self) -> Dict[str, str]:
        """
        Retourne une copie du dictionnaire des players.

        Utile pour éviter les problèmes de verrouillage pendant le replay.
        """
        with self._lock:
            return dict(self._players)

    def replay_events(
        self,
        events: List[Dict],
        speed: float = 1.0,
        target_player: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Rejoue une liste d'événements vers les players enregistrés.

        Args:
            events: Liste des événements à rejouer
            speed: Vitesse de replay (0.1 à 10.0)
            target_player: Nom d'un player spécifique (optionnel)

        Returns:
            Dict avec {replayed_count, failed_count}
        """
        # Obtenir les players cibles
        players_to_replay = self.get_players_copy()

        if not players_to_replay:
            return {'replayed_count': 0, 'failed_count': 0, 'error': 'No players registered'}

        # Filtrer par player si spécifié
        if target_player:
            if target_player not in players_to_replay:
                return {'replayed_count': 0, 'failed_count': 0, 'error': f'Player {target_player} not found'}
            players_to_replay = {target_player: players_to_replay[target_player]}

        replayed_count = 0
        failed_count = 0

        print(f"🎬 Starting replay of {len(events)} events to {len(players_to_replay)} player(s)")

        for i, event in enumerate(events):
            # Calculer le délai entre événements
            if i > 0:
                delay_ms = event['timestamp_offset_ms'] - events[i - 1]['timestamp_offset_ms']
                delay_seconds = (delay_ms / 1000.0) / speed
                if delay_seconds > 0:
                    time.sleep(delay_seconds)

            # Envoyer à tous les players cibles
            for player_name, player_endpoint in players_to_replay.items():
                try:
                    response = requests.post(
                        player_endpoint,
                        json={
                            'event_name': event['event_name'],
                            'event_data': event['event_data'],
                            'source': event.get('source', 'DevToolsReplay')
                        },
                        timeout=5
                    )
                    response.raise_for_status()
                    replayed_count += 1
                except requests.RequestException as e:
                    print(f"❌ Failed to replay event to {player_name}: {e}")
                    failed_count += 1

        print(f"✓ Replay completed: {replayed_count} events replayed, {failed_count} failed")

        return {
            'replayed_count': replayed_count,
            'failed_count': failed_count
        }
