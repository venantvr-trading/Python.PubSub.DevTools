"""
Event Listener - Écoute tous les événements du PubSub pour l'enregistrement.
"""
import threading
from typing import Optional

from python_pubsub_client import PubSubClient


class EventListener:
    """
    Écoute tous les événements du service bus et les enregistre.

    Ce listener utilise le wildcard "*" pour s'abonner à TOUS les topics.
    Il tourne dans un thread séparé (daemon) pour ne pas bloquer l'application principale.
    """

    def __init__(
        self,
        pubsub_url: str,
        recording_manager,
        consumer_name: str = "EventRecorder"
    ):
        """
        Initialise le listener.

        Args:
            pubsub_url: URL du serveur PubSub
            recording_manager: Instance de RecordingManager pour enregistrer les événements
            consumer_name: Nom du consumer (pour identification)
        """
        self._pubsub_url = pubsub_url
        self._recording_manager = recording_manager
        self._consumer_name = consumer_name
        self._client: Optional[PubSubClient] = None
        self._listener_thread: Optional[threading.Thread] = None
        self._running = False

    def _on_message(self, enriched_message: dict) -> None:
        """
        Callback appelé quand un message est reçu via wildcard.

        Pour les handlers wildcard, le client enrichit automatiquement le payload JSON
        avec les métadonnées du message (topic, producer, message_id).

        Args:
            enriched_message: Objet enrichi contenant:
                - topic: Nom du topic
                - message: Payload du message
                - producer: Nom du producteur
                - message_id: ID unique du message
        """
        try:
            topic = enriched_message.get("topic")
            data = enriched_message.get("message")
            producer = enriched_message.get("producer", "Unknown")

            if not topic:
                print(f"⚠ Received message without topic, skipping")
                return

            # Enregistrer l'événement
            self._recording_manager.record_event(
                event_name=topic,
                event_data=data,
                source=producer
            )

        except Exception as e:
            print(f"❌ Error recording event: {e}")
            import traceback
            traceback.print_exc()

    def start(self) -> bool:
        """
        Démarre le listener dans un thread séparé (daemon).

        Returns:
            True si démarré avec succès, False sinon
        """
        if self._running:
            print("⚠ Listener already running")
            return False

        try:
            print(f"🔄 Starting Event Listener...")
            print(f"   PubSub URL: {self._pubsub_url}")
            print(f"   Consumer: {self._consumer_name}")

            # Créer le client PubSub avec wildcard "*" pour écouter TOUS les topics
            self._client = PubSubClient(
                url=self._pubsub_url,
                consumer=self._consumer_name,
                topics=["*"]  # Wildcard pour tous les topics
            )
            print(f"   ✓ PubSub client created")

            # Enregistrer le handler pour tous les messages
            self._client.register_handler("*", self._on_message)
            print(f"   ✓ Handler registered for wildcard '*'")

            # Lancer le client dans un thread daemon
            self._running = True
            self._listener_thread = threading.Thread(
                target=self._run_client,
                daemon=True,
                name="EventListener"
            )
            self._listener_thread.start()
            print(f"   ✓ Listener thread started")

            print(f"✓ Event Listener started (listening to ALL topics via wildcard '*')")
            return True

        except Exception as e:
            print(f"❌ Failed to start Event Listener: {e}")
            import traceback
            traceback.print_exc()
            self._running = False
            return False

    def _run_client(self) -> None:
        """Thread worker qui exécute le client PubSub."""
        try:
            print(f"🔌 Connecting to PubSub Server at {self._pubsub_url}...")
            if self._client:
                self._client.start()  # Bloquant - se connecte et attend les messages
                print(f"✓ PubSub client connected successfully")
        except Exception as e:
            print(f"❌ Event Listener error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._running = False
            print(f"⚠ Event Listener thread terminated")

    def stop(self) -> None:
        """Arrête le listener."""
        if not self._running:
            print("⚠ Listener not running")
            return

        print("Stopping Event Listener...")
        self._running = False

        if self._client:
            try:
                self._client.stop()
            except Exception as e:
                print(f"⚠ Error stopping client: {e}")

        if self._listener_thread and self._listener_thread.is_alive():
            # Attendre max 5 secondes
            self._listener_thread.join(timeout=5)

        print("✓ Event Listener stopped")

    def is_running(self) -> bool:
        """Vérifie si le listener est actif."""
        return self._running
