"""
CLI unifié pour le lancement des services web PubSub DevTools.

Ce CLI simplifié utilise un fichier de configuration YAML unique pour tous les services.
"""
from __future__ import annotations

import sys
from pathlib import Path

import click

# Support pour exécution directe (développement PyCharm)
if __name__ == '__main__' and not __package__:
    # __package__ peut être None ou '' lors d'exécution directe
    # Ajouter le répertoire src au path pour permettre les imports
    import os

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    from python_pubsub_devtools.config import DevToolsConfig
else:
    from ..config import DevToolsConfig


@click.group()
@click.version_option()
def cli():
    """
    PubSub DevTools CLI - Outils de développement pour architectures événementielles.

    Lance les services web pour la visualisation des flux d'événements,
    l'enregistrement/rejeu, la simulation de marché et les tests de scénarios.

    Configuration:
        Utilisez un fichier YAML unique (par défaut: devtools_config.yaml)
        pour configurer tous les services. Exemple:

        \b
        agents_dir: "./agents"
        events_dir: "./events"
        recordings_dir: "./recordings"
        scenarios_dir: "./scenarios"
        reports_dir: "./reports"

        \b
        event_flow:
          port: 5555

        \b
        event_recorder:
          port: 5556

        \b
        mock_exchange:
          port: 5557

        \b
        scenario_testing:
          port: 5558
    """
    pass


@cli.command()
@click.option(
    '--config',
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default='devtools_config.yaml',
    help='Chemin vers le fichier de configuration YAML (défaut: devtools_config.yaml)'
)
@click.option(
    '--host',
    type=str,
    default='0.0.0.0',
    help='Adresse d\'écoute (défaut: 0.0.0.0)'
)
@click.option(
    '--debug/--no-debug',
    default=True,
    help='Activer le mode debug (défaut: activé)'
)
def event_flow(config: Path, host: str, debug: bool):
    """
    Lance le service Event Flow Visualization.

    Visualise les flux d'événements entre les agents de votre système.
    """
    from python_pubsub_devtools.event_flow.server import EventFlowServer

    try:
        cfg = DevToolsConfig.from_yaml(config)
        server = EventFlowServer(cfg.event_flow)
        server.run(host=host, debug=debug)
    except FileNotFoundError as e:
        click.echo(f"❌ Erreur: {e}", err=True)
        click.echo(f"\n💡 Créez un fichier de configuration avec: pubsub-tools config-example", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n👋 Event Flow server stopped")
        sys.exit(0)


@cli.command()
@click.option(
    '--config',
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default='devtools_config.yaml',
    help='Chemin vers le fichier de configuration YAML (défaut: devtools_config.yaml)'
)
@click.option(
    '--host',
    type=str,
    default='0.0.0.0',
    help='Adresse d\'écoute (défaut: 0.0.0.0)'
)
@click.option(
    '--debug/--no-debug',
    default=True,
    help='Activer le mode debug (défaut: activé)'
)
def event_recorder(config: Path, host: str, debug: bool):
    """
    Lance le service Event Recorder Dashboard.

    Parcourt et rejoue les sessions d'événements enregistrées.
    """
    from python_pubsub_devtools.event_recorder.server import EventRecorderServer

    try:
        cfg = DevToolsConfig.from_yaml(config)
        server = EventRecorderServer(cfg.event_recorder)
        server.run(host=host, debug=debug)
    except FileNotFoundError as e:
        click.echo(f"❌ Erreur: {e}", err=True)
        click.echo(f"\n💡 Créez un fichier de configuration avec: pubsub-tools config-example", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n👋 Event Recorder server stopped")
        sys.exit(0)


@cli.command()
@click.option(
    '--config',
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default='devtools_config.yaml',
    help='Chemin vers le fichier de configuration YAML (défaut: devtools_config.yaml)'
)
@click.option(
    '--host',
    type=str,
    default='0.0.0.0',
    help='Adresse d\'écoute (défaut: 0.0.0.0)'
)
def mock_exchange(config: Path, host: str):
    """
    Lance le service Mock Exchange Simulator.

    Simule un marché avec différents scénarios (tendance, volatilité, etc.).
    """
    from python_pubsub_devtools.mock_exchange.server import MockExchangeServer

    try:
        cfg = DevToolsConfig.from_yaml(config)
        server = MockExchangeServer(cfg.mock_exchange)
        server.run(host=host, debug=False)
    except FileNotFoundError as e:
        click.echo(f"❌ Erreur: {e}", err=True)
        click.echo(f"\n💡 Créez un fichier de configuration avec: pubsub-tools config-example", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n👋 Mock Exchange server stopped")
        sys.exit(0)


@cli.command()
@click.option(
    '--config',
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default='devtools_config.yaml',
    help='Chemin vers le fichier de configuration YAML (défaut: devtools_config.yaml)'
)
@click.option(
    '--host',
    type=str,
    default='0.0.0.0',
    help='Adresse d\'écoute (défaut: 0.0.0.0)'
)
def scenario_testing(config: Path, host: str):
    """
    Lance le service Scenario Testing Dashboard.

    Exécute et surveille des tests de scénarios avec chaos engineering.
    """
    from python_pubsub_devtools.scenario_testing.server import ScenarioTestingServer

    try:
        cfg = DevToolsConfig.from_yaml(config)
        if not cfg.scenario_testing:
            click.echo("❌ Erreur: scenario_testing non configuré dans le fichier YAML", err=True)
            sys.exit(1)
        server = ScenarioTestingServer(cfg.scenario_testing)
        server.run(host=host, debug=False)
    except FileNotFoundError as e:
        click.echo(f"❌ Erreur: {e}", err=True)
        click.echo(f"\n💡 Créez un fichier de configuration avec: pubsub-tools config-example", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n👋 Scenario Testing server stopped")
        sys.exit(0)


@cli.command()
@click.option(
    '--config',
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default='devtools_config.yaml',
    help='Chemin vers le fichier de configuration YAML (défaut: devtools_config.yaml)'
)
def serve_all(config: Path):
    """
    Lance tous les services DevTools simultanément.

    Démarre Event Flow, Event Recorder, Mock Exchange et Scenario Testing en parallèle.
    """
    import multiprocessing
    from python_pubsub_devtools.event_flow.server import EventFlowServer
    from python_pubsub_devtools.event_recorder.server import EventRecorderServer
    from python_pubsub_devtools.mock_exchange.server import MockExchangeServer
    from python_pubsub_devtools.scenario_testing.server import ScenarioTestingServer

    try:
        cfg = DevToolsConfig.from_yaml(config)
    except FileNotFoundError as e:
        click.echo(f"❌ Erreur: {e}", err=True)
        click.echo(f"\n💡 Créez un fichier de configuration avec: pubsub-tools config-example", err=True)
        sys.exit(1)

    def run_event_flow():
        server = EventFlowServer(cfg.event_flow)
        server.run(host='0.0.0.0', debug=False)

    def run_event_recorder():
        server = EventRecorderServer(cfg.event_recorder)
        server.run(host='0.0.0.0', debug=False)

    def run_mock_exchange():
        server = MockExchangeServer(cfg.mock_exchange)
        server.run(host='0.0.0.0', debug=False)

    def run_scenario_testing():
        if cfg.scenario_testing:
            server = ScenarioTestingServer(cfg.scenario_testing)
            server.run(host='0.0.0.0', debug=False)

    click.echo("=" * 80)
    click.echo("🚀 Démarrage de tous les services PubSub DevTools...")
    click.echo("=" * 80)
    click.echo(f"📊 Event Flow:        http://localhost:{cfg.event_flow.port}")
    click.echo(f"🎬 Event Recorder:    http://localhost:{cfg.event_recorder.port}")
    click.echo(f"🎰 Mock Exchange:     http://localhost:{cfg.mock_exchange.port}")
    if cfg.scenario_testing:
        click.echo(f"🎯 Scenario Testing:  http://localhost:{cfg.scenario_testing.port}")
    click.echo()
    click.echo("Appuyez sur Ctrl+C pour arrêter tous les services")
    click.echo("=" * 80)
    click.echo()

    # Créer les processus pour chaque service
    processes = []

    processes.append(multiprocessing.Process(target=run_event_flow))
    processes.append(multiprocessing.Process(target=run_event_recorder))
    processes.append(multiprocessing.Process(target=run_mock_exchange))
    if cfg.scenario_testing:
        processes.append(multiprocessing.Process(target=run_scenario_testing))

    try:
        # Démarrer tous les processus
        for p in processes:
            p.start()

        # Attendre tous les processus
        for p in processes:
            p.join()

    except KeyboardInterrupt:
        click.echo("\n👋 Arrêt de tous les services...")
        for p in processes:
            if p.is_alive():
                p.terminate()
                p.join(timeout=5)
        click.echo("✅ Tous les services sont arrêtés")
        sys.exit(0)


@cli.command()
@click.option(
    '--output',
    '-o',
    type=click.Path(dir_okay=False, path_type=Path),
    help='Chemin pour sauvegarder la configuration (optionnel)'
)
def config_example(output: Path | None):
    """
    Affiche un exemple de fichier de configuration YAML.

    Crée un fichier devtools_config.yaml prêt à l'emploi avec tous les services.
    """
    example = """# Configuration PubSub DevTools
# Fichier de configuration centralisé pour tous les services

# === Répertoires Communs ===
# Chemins relatifs (par rapport à ce fichier) ou absolus
agents_dir: "./agents"
events_dir: "./events"
recordings_dir: "./recordings"
scenarios_dir: "./scenarios"
reports_dir: "./reports"

# === Event Flow Visualization ===
event_flow:
  port: 5555

  # Agents à exclure de la visualisation (agents de test/utilitaires)
  test_agents:
    - "token_balance_refresh"

  # Couleurs par namespace pour la catégorisation
  namespace_colors:
    bot_lifecycle: "#81c784"    # vert
    market_data: "#64b5f6"      # bleu
    indicator: "#9575cd"        # violet
    internal: "#ba68c8"         # violet clair
    capital: "#ffd54f"          # jaune
    pool: "#ffb74d"             # orange
    position: "#ff8a65"         # orange foncé
    exchange: "#4dd0e1"         # cyan
    command: "#a1887f"          # marron
    database: "#90a4ae"         # gris bleu
    exit_strategy: "#aed581"    # vert clair
    query: "#81d4fa"            # bleu clair
    unknown: "#e0e0e0"          # gris

# === Event Recorder ===
event_recorder:
  port: 5556

# === Mock Exchange Simulator ===
mock_exchange:
  port: 5557
  default_initial_price: 50000.0
  default_volatility: 0.02
  default_spread_bps: 10.0

# === Scenario Testing ===
scenario_testing:
  port: 5558

# === Structure de Répertoires Recommandée ===
# project/
# ├── devtools_config.yaml  # Ce fichier
# ├── agents/               # Fichiers Python des agents
# │   ├── market_agent.py
# │   ├── risk_agent.py
# │   └── execution_agent.py
# ├── events/               # Fichiers JSON des événements
# │   ├── MarketDataReceived.json
# │   ├── RiskAssessed.json
# │   └── OrderExecuted.json
# ├── recordings/           # Sessions d'enregistrement
# ├── scenarios/            # Scénarios de test YAML
# └── reports/              # Rapports de tests

# === Utilisation ===
# CLI:
#   pubsub-tools event-flow --config devtools_config.yaml
#   pubsub-tools event-recorder --config devtools_config.yaml
#   pubsub-tools mock-exchange --config devtools_config.yaml
#   pubsub-tools scenario-testing --config devtools_config.yaml
#   pubsub-tools serve-all --config devtools_config.yaml
#
# Python:
#   from python_pubsub_devtools.config import DevToolsConfig
#   config = DevToolsConfig.from_yaml("devtools_config.yaml")
#
#   # Utilisation programmatique
#   from python_pubsub_devtools.event_flow.server import EventFlowServer
#   server = EventFlowServer(config.event_flow)
#   server.run()
"""

    if output:
        try:
            output.write_text(example)
            click.echo(f"✅ Configuration sauvegardée dans: {output}")
        except Exception as e:
            click.echo(f"❌ Erreur lors de la sauvegarde: {e}", err=True)
            sys.exit(1)
    else:
        click.echo(example)


if __name__ == '__main__':
    cli()
