"""
Mock Exchange Server - Flask application wrapper for Mock Exchange simulator.

Manages web interface and API for candlestick replay files.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import Flask


def create_app(config: Any) -> Flask:
    """
    Crée et configure l'application Flask pour Mock Exchange.

    Args:
        config: MockExchangeConfig avec replay_data_dir et autres paramètres

    Returns:
        Flask app configurée
    """
    # Configure Flask pour trouver templates et static dans le répertoire web parent
    tools_dir = Path(__file__).parent.parent
    app = Flask(__name__,
                template_folder=str(tools_dir / 'web' / 'templates'),
                static_folder=str(tools_dir / 'web' / 'static'))

    # Configuration
    app.config['REPLAY_DATA_DIR'] = config.replay_data_dir
    app.config['PORT'] = config.port

    # Importer les modules nécessaires
    from .scenario_exchange import ScenarioBasedMockExchange
    from . import views

    # Initialiser le moteur de simulation
    engine = ScenarioBasedMockExchange(
        replay_data_dir=config.replay_data_dir,
        pubsub_url=config.pubsub_url,
        candle_topic=config.candle_topic,
        get_receivers_callback=views.get_registered_receivers  # Conservé pour compatibilité
    )
    app.config['EXCHANGE_ENGINE'] = engine

    # S'assurer que le répertoire existe
    if config.replay_data_dir:
        config.replay_data_dir.mkdir(parents=True, exist_ok=True)

    # Enregistrer les routes
    views.register_routes(app)

    return app


class MockExchangeServer:
    """Server for Mock Exchange Simulator"""

    def __init__(self, config: Any):
        """
        Initialise le serveur avec la configuration.

        Args:
            config: MockExchangeConfig object avec replay_data_dir, port, pubsub_url, etc.
        """
        self.config = config
        self.port = config.port
        self.replay_data_dir = getattr(config, 'replay_data_dir', None)

        # Créer l'application Flask
        self.app = create_app(config)

    def run(self, host: str = '0.0.0.0', debug: bool = False) -> None:
        """
        Lance le serveur Flask.

        Args:
            host: Adresse d'écoute (default: 0.0.0.0)
            debug: Active le mode debug (default: False)
        """
        print("=" * 80)
        print("🎰 Mock Exchange Simulator Server")
        print("=" * 80)
        print()
        if self.replay_data_dir:
            print(f"📂 Replay data directory: {self.replay_data_dir}")
        print()
        print(f"🌐 Server running at: http://{host}:{self.port}")
        print()
        print("   Press Ctrl+C to stop")
        print("=" * 80)
        print()

        self.app.run(host=host, port=self.port, debug=debug)
