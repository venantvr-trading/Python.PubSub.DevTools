"""
Mock Exchange Server - Serveur web pour le simulateur de marché.
"""
from __future__ import annotations

from pathlib import Path

from flask import Flask

from ..config import MockExchangeConfig


def create_app(config: MockExchangeConfig) -> Flask:
    """Crée l'application Flask pour Mock Exchange.

    Application Factory pattern pour permettre l'initialisation avec configuration.

    Args:
        config: Configuration MockExchangeConfig

    Returns:
        Instance Flask configurée
    """
    # Configure Flask pour trouver templates et static dans le répertoire web parent
    tools_dir = Path(__file__).parent.parent
    app = Flask(
        __name__,
        template_folder=str(tools_dir / 'web' / 'templates'),
        static_folder=str(tools_dir / 'web' / 'static')
    )

    # Stocker la configuration dans l'app
    app.config['PORT'] = config.port
    app.config['DEFAULT_INITIAL_PRICE'] = config.default_initial_price
    app.config['DEFAULT_VOLATILITY'] = config.default_volatility
    app.config['DEFAULT_SPREAD_BPS'] = config.default_spread_bps

    # Importer et enregistrer les routes
    from . import views
    views.register_routes(app)

    return app


class MockExchangeServer:
    """Serveur pour le simulateur Mock Exchange.

    Ce serveur fournit une interface web pour lancer et visualiser des simulations
    de marché en temps réel avec différents scénarios (tendance, volatilité, etc.).

    Example:
        >>> from python_pubsub_devtools.config import MockExchangeConfig
        >>>
        >>> config = MockExchangeConfig(
        ...     port=5557,
        ...     default_initial_price=50000.0,
        ...     default_volatility=0.02
        ... )
        >>> server = MockExchangeServer(config)
        >>> server.run()  # Bloquant
    """

    def __init__(self, config: MockExchangeConfig):
        """Initialise le serveur avec la configuration.

        Args:
            config: Configuration MockExchangeConfig avec paramètres du simulateur
        """
        self.config = config
        self.port = config.port
        self.app = create_app(config)

    def run(self, host: str = '0.0.0.0', debug: bool = False) -> None:
        """Lance le serveur Flask (bloquant).

        Cette méthode est bloquante. Pour une utilisation dans un processus séparé,
        appelez cette méthode dans un thread ou un processus multiprocessing.

        Note:
            Le mode debug est désactivé par défaut car ce service utilise des threads
            pour les simulations. En mode debug, Flask recharge l'app ce qui peut
            causer des problèmes avec les threads.

        Args:
            host: Adresse d'écoute (défaut: 0.0.0.0)
            debug: Mode debug Flask (défaut: False)
        """
        print("=" * 80)
        print("🎰 Mock Exchange Simulator Dashboard")
        print("=" * 80)
        print()
        print(f"💰 Initial price: ${self.config.default_initial_price:,.2f}")
        print(f"📊 Default volatility: {self.config.default_volatility:.2%}")
        print(f"📏 Default spread: {self.config.default_spread_bps:.1f} bps")
        print()
        print(f"🌐 Server running at: http://{host}:{self.port}")
        print()
        print("   Press Ctrl+C to stop")
        print("=" * 80)
        print()

        # threaded=True est nécessaire pour gérer les simulations en background
        self.app.run(host=host, port=self.port, debug=debug, threaded=True)
