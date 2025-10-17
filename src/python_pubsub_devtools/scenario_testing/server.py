"""
Scenario Testing Server - Serveur web pour l'exécution de tests de scénarios.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import Flask, g

from ..config import ScenarioTestingConfig


def create_app(config: ScenarioTestingConfig) -> Flask:
    """Crée l'application Flask pour Scenario Testing.

    Application Factory pattern pour permettre l'initialisation avec configuration.

    Args:
        config: Configuration ScenarioTestingConfig

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
    app.config['SCENARIOS_DIR'] = config.scenarios_dir
    app.config['REPORTS_DIR'] = config.reports_dir
    app.config['PORT'] = config.port

    # S'assurer que les répertoires existent
    config.scenarios_dir.mkdir(parents=True, exist_ok=True)
    config.reports_dir.mkdir(parents=True, exist_ok=True)

    @app.before_request
    def before_request():
        # Stocker les dépendances dans le contexte global de la requête (g)
        # C'est une façon propre de rendre les dépendances disponibles dans les vues.
        g.service_bus = app.config.get('SERVICE_BUS')

    # Importer et enregistrer les routes
    from . import views

    views.register_routes(app)

    return app


class ScenarioTestingServer:
    """Serveur pour le tableau de bord Scenario Testing.

    Ce serveur fournit une interface web pour exécuter et surveiller des tests
    de scénarios avec ingénierie du chaos et assertions.

    Example:
        >>> from python_pubsub_devtools.config import ScenarioTestingConfig
        >>> from pathlib import Path
        >>>
        >>> config = ScenarioTestingConfig(
        ...     scenarios_dir=Path("./scenarios"),
        ...     reports_dir=Path("./reports"),
        ...     port=5558
        ... )
        >>> server = ScenarioTestingServer(config)
        >>> server.run()  # Bloquant
    """

    def __init__(self, config: ScenarioTestingConfig, service_bus: Any):
        """Initialise le serveur avec la configuration.

        Args:
            config: Configuration ScenarioTestingConfig avec répertoires et port
            service_bus: Instance du bus de services pour l'injection de chaos
                et l'écoute d'événements.
        """
        self.config = config
        self.scenarios_dir = config.scenarios_dir
        self.reports_dir = config.reports_dir
        self.service_bus = service_bus
        self.port = config.port

        self.app = create_app(config)

    def run(self, host: str = '0.0.0.0', debug: bool = False) -> None:
        """Lance le serveur Flask (bloquant).

        Cette méthode est bloquante. Pour une utilisation dans un processus séparé,
        appelez cette méthode dans un thread ou un processus multiprocessing.

        Note:
            Le mode debug est désactivé par défaut car ce service utilise des threads
            pour l'exécution des tests. En mode debug, Flask recharge l'app ce qui
            peut causer des problèmes avec les threads.

        Args:
            host: Adresse d'écoute (défaut: 0.0.0.0)
            debug: Mode debug Flask (défaut: False)
        """
        # Compter les scénarios disponibles
        scenario_count = len(list(self.scenarios_dir.glob('*.yaml')))

        print("=" * 80)
        print("🎯 Scenario Testing Dashboard")
        print("=" * 80)
        print()
        print(f"📁 Scenarios directory: {self.scenarios_dir}")
        print(f"   Found {scenario_count} scenarios")
        print(f"📊 Reports directory: {self.reports_dir}")
        print()
        print(f"🌐 Server running at: http://{host}:{self.port}")
        print()
        print("   Press Ctrl+C to stop")
        print("=" * 80)
        print()

        # Injecter le service_bus dans la configuration de l'app
        self.app.config['SERVICE_BUS'] = self.service_bus

        # threaded=True est nécessaire pour gérer les tests en background
        self.app.run(host=host, port=self.port, debug=debug, threaded=True)
