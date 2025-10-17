"""
Event Recorder Server - Serveur web pour la visualisation des enregistrements d'événements.
"""
from __future__ import annotations

from pathlib import Path

from flask import Flask

from ..config import EventRecorderConfig


def create_app(config: EventRecorderConfig) -> Flask:
    """Crée l'application Flask pour Event Recorder.

    Application Factory pattern pour permettre l'initialisation avec configuration.

    Args:
        config: Configuration EventRecorderConfig

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
    app.config['RECORDINGS_DIR'] = config.recordings_dir
    app.config['PORT'] = config.port

    # S'assurer que le répertoire existe
    config.recordings_dir.mkdir(parents=True, exist_ok=True)

    # Importer et enregistrer les routes
    from . import views

    views.register_routes(app)

    return app


class EventRecorderServer:
    """Serveur pour le tableau de bord Event Recorder.

    Ce serveur fournit une interface web pour parcourir et visualiser
    les enregistrements d'événements capturés.

    Example (mode simulation):
        >>> from python_pubsub_devtools.config import EventRecorderConfig
        >>> from pathlib import Path
        >>>
        >>> config = EventRecorderConfig(
        ...     recordings_dir=Path("./recordings"),
        ...     port=5556
        ... )
        >>> server = EventRecorderServer(config)
        >>> server.run()  # Mode simulation uniquement

    Example (avec ServiceBus pour replay réel):
        Le replay réel (publication sur un bus) doit maintenant être fait
        programmatiquement en utilisant la classe EventReplayer, et non via le serveur.
    """

    def __init__(self, config: EventRecorderConfig):
        """Initialise le serveur avec la configuration.

        Args:
            config: Configuration EventRecorderConfig avec recordings_dir et port
        """
        self.config = config
        self.recordings_dir = config.recordings_dir
        self.port = config.port
        self.app = create_app(config)

    def run(self, host: str = '0.0.0.0', debug: bool = True) -> None:
        """Lance le serveur Flask (bloquant).

        Cette méthode est bloquante. Pour une utilisation dans un processus séparé,
        appelez cette méthode dans un thread ou un processus multiprocessing.

        Args:
            host: Adresse d'écoute (défaut: 0.0.0.0)
            debug: Mode debug Flask (défaut: True)
        """
        # Compter les enregistrements
        recording_count = len(list(self.recordings_dir.glob('*.json')))

        print("=" * 80)
        print("🎬 Event Recorder Dashboard")
        print("=" * 80)
        print()
        print(f"📁 Recordings directory: {self.recordings_dir}")
        print(f"   Found {recording_count} recordings")
        print()
        print(f"🌐 Server running at: http://{host}:{self.port}")
        print()
        print("   Press Ctrl+C to stop")
        print("=" * 80)
        print()

        self.app.run(host=host, port=self.port, debug=debug)
