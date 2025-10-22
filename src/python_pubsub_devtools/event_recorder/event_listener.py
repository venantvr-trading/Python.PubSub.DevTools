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

    def _on_message(self, message: dict) -> None:
        """
        Callback appelé quand un message est reçu.

        Args:
            message: Message PubSub contenant topic, message, producer, message_id
        """
        try:
            topic = message.get("topic")
            data = message.get("message")
            producer = message.get("producer", "Unknown")

            # Enregistrer l'événement
            self._recording_manager.record_event(
                event_name=topic,
                event_data=data,
                source=producer
            )

        except Exception as e:
            print(f"❌ Error recording event: {e}")

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
            # Créer le client PubSub avec wildcard "*" pour écouter TOUS les topics
            self._client = PubSubClient(
                url=self._pubsub_url,
                consumer=self._consumer_name,
                topics=["*"]  # Wildcard pour tous les topics
            )

            # Enregistrer le handler pour tous les messages
            self._client.on("*", self._on_message)

            # Lancer le client dans un thread daemon
            self._running = True
            self._listener_thread = threading.Thread(
                target=self._run_client,
                daemon=True,
                name="EventListener"
            )
            self._listener_thread.start()

            print(f"✓ Event Listener started (listening to ALL topics via wildcard '*')")
            return True

        except Exception as e:
            print(f"❌ Failed to start Event Listener: {e}")
            self._running = False
            return False

    def _run_client(self) -> None:
        """Thread worker qui exécute le client PubSub."""
        try:
            if self._client:
                self._client.start()  # Bloquant
        except Exception as e:
            print(f"❌ Event Listener error: {e}")
        finally:
            self._running = False

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
