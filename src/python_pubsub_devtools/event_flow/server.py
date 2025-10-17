"""
Event Flow Server - Serveur web pour la visualisation des flux d'événements.
"""
from __future__ import annotations

from .serve_event_flow import create_app


class EventFlowServer:
    """Serveur pour la visualisation des flux d'événements."""

    def __init__(self, config):
        """Initialise le serveur avec la configuration.

        Args:
            config: Objet EventFlowConfig.
        """
        self.config = config
        self.port = config.port

        # Créer l'application Flask en utilisant la factory
        self.app = create_app(config)

    def run(self, host='0.0.0.0', debug=True):
        """Lance le serveur Flask (bloquant).

        Args:
            host: Adresse d'écoute (défaut: 0.0.0.0)
            debug: Activer le mode debug (défaut: True)
        """
        print("=" * 80)
        print("🚀 Event Flow Visualization Server")
        print("=" * 80)
        print()
        print(f"🌐 Server running at: http://{host}:{self.port}")
        print("   Le serveur attend que le 'scanner' lui envoie les données du graphe.")
        print()
        print("   Press Ctrl+C to stop")
        print("=" * 80)
        print()

        self.app.run(host=host, port=self.port, debug=debug)
