"""
Gestion des players enregistrés pour le replay d'événements.
"""
from __future__ import annotations

import threading
import time
import uuid
from typing import Dict, List, Optional

from python_pubsub_client import PubSubClient


class PlayerManager:
    """
    Gestionnaire pour la publication d'événements sur le service bus.

    Responsabilités:
    - Publication d'événements sur le service bus pour replay
    """

    def __init__(self, pubsub_url: str = "http://localhost:5000", producer_name: str = "EventRecorderReplay"):
        """
        Initialise le PlayerManager.

        Args:
            pubsub_url: URL du serveur PubSub
            producer_name: Nom du producteur pour les événements rejoués
        """
        self._pubsub_url = pubsub_url
        self._producer_name = producer_name
        self._pubsub_client: Optional[PubSubClient] = None
        self._stop_replay = threading.Event()  # Flag pour arrêter le replay
        self._pause_replay = threading.Event()  # Flag pour pause
        self._pause_replay.set()  # Par défaut, pas en pause
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
            # Démarrer le client dans un thread séparé pour ne pas bloquer Flask
            client_thread = threading.Thread(
                target=self._pubsub_client.start,
                daemon=True,
                name="PubSubClientThread"
            )
            client_thread.start()
            print(f"✓ PubSub client initialized and started: {self._pubsub_url}")
        except Exception as e:
            print(f"⚠ Failed to initialize PubSub client: {e}")
            self._pubsub_client = None

    def shutdown(self) -> None:
        """
        Arrête proprement le client PubSub.
        À appeler lors de la fermeture de l'application.
        """
        if self._pubsub_client:
            try:
                self._pubsub_client.stop()
                print(f"✓ PubSub client stopped")
            except Exception as e:
                print(f"⚠ Error stopping PubSub client: {e}")

    def stop_replay(self) -> None:
        """Arrête le replay en cours."""
        self._stop_replay.set()
        print("⏹️ Stop replay requested")

    def pause_replay(self, paused: bool) -> None:
        """Met en pause ou reprend le replay.

        Args:
            paused: True pour mettre en pause, False pour reprendre
        """
        if paused:
            self._pause_replay.clear()
            print("⏸️ Replay paused")
        else:
            self._pause_replay.set()
            print("▶️ Replay resumed")

    def replay_events(
            self,
            events: List[Dict],
            speed: float = 1.0,
            target_player: Optional[str] = None,
            progress_callback: Optional[callable] = None
    ) -> Dict[str, int]:
        """
        Rejoue une liste d'événements via le service bus.

        Les événements sont publiés sur leurs topics respectifs et seront
        reçus par tous les consumers abonnés à ces topics.

        Args:
            events: Liste des événements à rejouer
            speed: Vitesse de replay (0.1 à 10.0)
            target_player: Non utilisé (conservé pour compatibilité)
            progress_callback: Fonction appelée à chaque événement avec (index, total)

        Returns:
            Dict avec {replayed_count, failed_count}
        """
        if not self._pubsub_client:
            return {
                'replayed_count': 0,
                'failed_count': 0,
                'error': 'PubSub client not initialized'
            }

        # Réinitialiser les flags
        self._stop_replay.clear()
        self._pause_replay.set()

        replayed_count = 0
        failed_count = 0
        event_name = "Unknown"

        print(f"🎬 Starting replay of {len(events)} events via PubSub at {speed}x speed")

        for i, event in enumerate(events):
            # Vérifier si on doit arrêter
            if self._stop_replay.is_set():
                print(f"⏹️ Replay stopped at event {i + 1}/{len(events)}")
                break

            # Attendre si en pause
            self._pause_replay.wait()

            # Calculer le délai entre événements
            if i > 0:
                delay_ms = event['timestamp_offset_ms'] - events[i - 1]['timestamp_offset_ms']
                delay_seconds = (delay_ms / 1000.0) / speed

                # Découper le sleep pour permettre une réponse plus rapide au stop
                if delay_seconds > 0:
                    sleep_chunks = max(1, int(delay_seconds * 10))  # 10 checks par seconde
                    chunk_duration = delay_seconds / sleep_chunks

                    for _ in range(sleep_chunks):
                        if self._stop_replay.is_set():
                            break
                        self._pause_replay.wait()
                        time.sleep(chunk_duration)

            # Vérifier à nouveau après le sleep
            if self._stop_replay.is_set():
                print(f"⏹️ Replay stopped at event {i + 1}/{len(events)}")
                break

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

                # Callback de progression
                if progress_callback:
                    progress_callback(i + 1, len(events))

                if (i + 1) % 10 == 0:
                    print(f"  Replayed {i + 1}/{len(events)} events...")

            except Exception as e:
                print(f"❌ Failed to replay event {event_name}: {e}")
                failed_count += 1

        if not self._stop_replay.is_set():
            print(f"✅ Replay completed: {replayed_count} events replayed, {failed_count} failed")
        else:
            print(f"⏹️ Replay interrupted: {replayed_count} events replayed, {failed_count} failed")

        return {
            'replayed_count': replayed_count,
            'failed_count': failed_count
        }
