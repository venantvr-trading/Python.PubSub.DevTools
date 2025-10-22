"""
Gestion des players enregistrés pour le replay d'événements.
"""
from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from python_pubsub_client import PubSubClient


class PlayerManager:
    """
    Gestionnaire centralisé des players enregistrés.

    Responsabilités:
    - Enregistrement/désenregistrement des players
    - Liste des players actifs
    - Publication d'événements sur le service bus pour replay
    """

    def __init__(self, pubsub_url: str = "http://localhost:5000", producer_name: str = "EventRecorderReplay"):
        """
        Initialise le PlayerManager.

        Args:
            pubsub_url: URL du serveur PubSub
            producer_name: Nom du producteur pour les événements rejoués
        """
        self._players: Dict[str, str] = {}  # consumer_name -> player_endpoint (obsolète mais gardé pour compatibilité)
        self._lock = threading.Lock()
        self._pubsub_url = pubsub_url
        self._producer_name = producer_name
        self._pubsub_client: Optional[PubSubClient] = None
        self._init_pubsub_client()

    def _init_pubsub_client(self) -> None:
        """
        Initialise le client PubSub pour la publication d'événements.
        Le client n'a pas besoin de s'abonner à des topics, uniquement de publier.
        """
        try:
            # Créer un client sans topics (publication uniquement)
            self._pubsub_client = PubSubClient(
                url=self._pubsub_url,
                consumer=self._producer_name,
                topics=[]  # Aucun topic à écouter, uniquement publication
            )
            print(f"✓ PubSub client initialized: {self._pubsub_url}")
        except Exception as e:
            print(f"⚠ Failed to initialize PubSub client: {e}")
            self._pubsub_client = None

    def register(self, consumer_name: str, player_endpoint: str) -> bool:
        """
        Enregistre un player endpoint (conservé pour compatibilité).

        Args:
            consumer_name: Nom du consumer
            player_endpoint: URL du endpoint player (non utilisé avec PubSub)

        Returns:
            True si enregistré avec succès
        """
        with self._lock:
            self._players[consumer_name] = player_endpoint
        print(f"✓ Player registered: {consumer_name} (using PubSub)")
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
        Rejoue une liste d'événements via le service bus.

        Les événements sont publiés sur leurs topics respectifs et seront
        reçus par tous les consumers abonnés à ces topics.

        Args:
            events: Liste des événements à rejouer
            speed: Vitesse de replay (0.1 à 10.0)
            target_player: Non utilisé (conservé pour compatibilité)

        Returns:
            Dict avec {replayed_count, failed_count}
        """
        if not self._pubsub_client:
            return {
                'replayed_count': 0,
                'failed_count': 0,
                'error': 'PubSub client not initialized'
            }

        replayed_count = 0
        failed_count = 0

        print(f"🎬 Starting replay of {len(events)} events via PubSub")

        for i, event in enumerate(events):
            # Calculer le délai entre événements
            if i > 0:
                delay_ms = event['timestamp_offset_ms'] - events[i - 1]['timestamp_offset_ms']
                delay_seconds = (delay_ms / 1000.0) / speed
                if delay_seconds > 0:
                    time.sleep(delay_seconds)

            # Publier l'événement sur le service bus
            try:
                event_name = event['event_name']
                event_data = event['event_data']
                message_id = str(uuid.uuid4())

                self._pubsub_client.publish(
                    topic=event_name,
                    message=event_data,
                    producer=self._producer_name,
                    message_id=message_id
                )
                replayed_count += 1

                if (i + 1) % 10 == 0:
                    print(f"  Replayed {i + 1}/{len(events)} events...")

            except Exception as e:
                print(f"❌ Failed to replay event {event_name}: {e}")
                failed_count += 1

        print(f"✓ Replay completed: {replayed_count} events replayed, {failed_count} failed")

        return {
            'replayed_count': replayed_count,
            'failed_count': failed_count
        }
