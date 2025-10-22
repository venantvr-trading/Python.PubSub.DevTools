#!/usr/bin/env python3
"""
Script de debug pour Event Recorder.

Permet de lancer event_recorder directement pour le débogage dans PyCharm.
Configure les chemins Python et charge la configuration par défaut.

Usage:
    python debug_event_recorder.py

PyCharm Debug:
    1. Ouvrir ce fichier dans PyCharm
    2. Clic droit -> Debug 'debug_event_recorder'
    3. Définir des breakpoints dans le code
"""
import sys
from pathlib import Path

# Ajouter src au Python path pour les imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from python_pubsub_devtools.config import DevToolsConfig
from python_pubsub_devtools.event_recorder.server import EventRecorderServer


def main():
    """Lance Event Recorder en mode debug."""

    # Chemin vers le fichier de configuration
    config_file = project_root / "devtools_config.yaml"

    if not config_file.exists():
        print(f"❌ Configuration file not found: {config_file}")
        print("\n💡 Create one with: pubsub-tools config-example -o devtools_config.yaml")
        sys.exit(1)

    # Charger la configuration
    print(f"📋 Loading configuration from: {config_file}")
    cfg = DevToolsConfig.from_yaml(config_file)

    # Créer et lancer le serveur
    print(f"🚀 Starting Event Recorder on port {cfg.event_recorder.port}")
    print(f"📁 Recordings directory: {cfg.event_recorder.recordings_dir}")
    print(f"🔗 PubSub URL: {cfg.event_recorder.pubsub_url}")
    print()

    server = EventRecorderServer(cfg.event_recorder)

    try:
        # Lancer en mode debug avec auto-reload
        server.run(host='0.0.0.0', debug=True)
    except KeyboardInterrupt:
        print("\n\n👋 Event Recorder stopped")
        sys.exit(0)


if __name__ == '__main__':
    main()
