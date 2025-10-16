"""
Exemple d'utilisation basique de PubSub DevTools.

Ce fichier démontre l'API programmatique de la bibliothèque, qui est l'interface
principale pour intégrer les outils dans vos propres scripts, tests ou IDE.
"""
import multiprocessing
from pathlib import Path

from python_pubsub_devtools.config import DevToolsConfig

# ============================================================================
# 1. CHARGER LA CONFIGURATION
# ============================================================================

# Méthode 1: Depuis un fichier YAML (recommandé)
# Les chemins relatifs dans le YAML sont résolus automatiquement
config = DevToolsConfig.from_yaml("devtools_config.yaml")

# Méthode 2: Depuis un dictionnaire Python
config_dict = {
    'agents_dir': '../path/to/your/agents',
    'events_dir': '../path/to/your/events',
    'recordings_dir': './recordings',
    'scenarios_dir': './scenarios',
    'reports_dir': './reports',
}
config_from_dict = DevToolsConfig.from_dict(config_dict)

# ============================================================================
# 2. ACCÉDER AUX CONFIGURATIONS SPÉCIFIQUES
# ============================================================================

# Chaque service a sa propre configuration
print("=== Configuration des Services ===")
print(f"Event Flow agents directory: {config.event_flow.agents_dir}")
print(f"Event Flow port: {config.event_flow.port}")
print(f"Event Recorder port: {config.event_recorder.port}")
print(f"Mock Exchange port: {config.mock_exchange.port}")
if config.scenario_testing:
    print(f"Scenario Testing port: {config.scenario_testing.port}")
print()


# ============================================================================
# 3. UTILISATION PROGRAMMATIQUE DES SERVEURS
# ============================================================================

# IMPORTANT: Chaque serveur expose une classe ...Server avec une méthode run()
# qui est bloquante (comme Flask app.run()). Pour une utilisation pratique,
# lancez les serveurs dans des processus séparés.

def example_launch_single_server():
    """Exemple: Lancer un seul serveur (bloquant)."""
    from python_pubsub_devtools.event_flow.server import EventFlowServer

    # Instancier le serveur avec la configuration
    server = EventFlowServer(config.event_flow)

    # Lancer le serveur (BLOQUANT)
    # Cette méthode ne retourne pas tant que le serveur tourne
    server.run(host='0.0.0.0', debug=True)


def example_launch_in_process():
    """Exemple: Lancer un serveur dans un processus séparé."""
    from python_pubsub_devtools.event_flow.server import EventFlowServer

    def run_server():
        server = EventFlowServer(config.event_flow)
        server.run(host='0.0.0.0', debug=False)

    # Créer un processus pour le serveur
    process = multiprocessing.Process(target=run_server)
    process.start()

    print(f"✅ Event Flow server démarré dans le processus {process.pid}")
    print(f"   Accès: http://localhost:{config.event_flow.port}")

    # Votre code peut continuer ici pendant que le serveur tourne...

    # Pour arrêter proprement:
    # process.terminate()
    # process.join()

    return process


def example_launch_multiple_servers():
    """Exemple: Lancer plusieurs serveurs en parallèle."""
    from python_pubsub_devtools.event_flow.server import EventFlowServer
    from python_pubsub_devtools.event_recorder.server import EventRecorderServer
    from python_pubsub_devtools.mock_exchange.server import MockExchangeServer

    def run_event_flow():
        server = EventFlowServer(config.event_flow)
        server.run(host='0.0.0.0', debug=False)

    def run_event_recorder():
        server = EventRecorderServer(config.event_recorder)
        server.run(host='0.0.0.0', debug=False)

    def run_mock_exchange():
        server = MockExchangeServer(config.mock_exchange)
        server.run(host='0.0.0.0', debug=False)

    # Créer les processus
    processes = [
        multiprocessing.Process(target=run_event_flow),
        multiprocessing.Process(target=run_event_recorder),
        multiprocessing.Process(target=run_mock_exchange),
    ]

    # Démarrer tous les serveurs
    for p in processes:
        p.start()

    print("✅ Tous les serveurs sont démarrés:")
    print(f"   📊 Event Flow:     http://localhost:{config.event_flow.port}")
    print(f"   🎬 Event Recorder: http://localhost:{config.event_recorder.port}")
    print(f"   🎰 Mock Exchange:  http://localhost:{config.mock_exchange.port}")

    # Attendre que tous les processus se terminent (ou les arrêter manuellement)
    # for p in processes:
    #     p.join()

    return processes


def example_launch_recorder_with_servicebus():
    """Exemple: Lancer Event Recorder avec ServiceBus pour replay réel."""
    from python_pubsub_devtools.event_recorder.server import EventRecorderServer

    # IMPORTANT: Créer votre instance ServiceBus
    # Remplacez cette ligne par votre propre ServiceBus
    # from your_app.service_bus import ServiceBus
    # service_bus = ServiceBus()

    # Pour cet exemple, on simule sans ServiceBus
    service_bus = None  # Remplacez par votre ServiceBus réel

    def run_recorder():
        # Passer le ServiceBus au serveur
        server = EventRecorderServer(config.event_recorder, service_bus=service_bus)
        server.run(host='0.0.0.0', debug=False)

    process = multiprocessing.Process(target=run_recorder)
    process.start()

    print("✅ Event Recorder démarré avec support ServiceBus:")
    print(f"   🎬 Dashboard: http://localhost:{config.event_recorder.port}")
    if service_bus:
        print("   ✓ Mode REAL: Replay publiera les événements sur le ServiceBus")
    else:
        print("   ⚠ Mode SIMULATION seulement (pas de ServiceBus fourni)")
    print()
    print("   Dans le dashboard, décochez 'Simulation Mode' pour activer le replay réel")

    return process


# ============================================================================
# 4. UTILISATION DE L'ANALYSEUR D'ÉVÉNEMENTS (sans serveur web)
# ============================================================================

def example_analyze_events():
    """Exemple: Analyser les événements sans lancer de serveur web."""
    from python_pubsub_devtools.event_flow import EventFlowAnalyzer

    # Créer l'analyseur avec le répertoire des agents
    analyzer = EventFlowAnalyzer(config.event_flow.agents_dir)

    # Analyser les événements
    analyzer.analyze()

    # Récupérer tous les événements
    events = analyzer.get_all_events()
    print(f"\nFound {len(events)} events in the system")

    # Afficher un résumé
    analyzer.print_summary()

    # Générer un diagramme Graphviz
    dot_content = analyzer.generate_graphviz()
    Path("event_flow.dot").write_text(dot_content)
    print("\n✅ Event flow diagram saved to event_flow.dot")
    print("   Generate image with: dot -Tpng event_flow.dot -o event_flow.png")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                   PubSub DevTools - Usage Examples                       ║
╚══════════════════════════════════════════════════════════════════════════╝

Ce script démontre différents cas d'usage de l'API programmatique.

CAS D'USAGE TYPIQUES:
1. Dans un script de test: Lancer les serveurs avant d'exécuter des tests
2. Dans un IDE: Démarrer les outils de debugging depuis votre environnement
3. Dans un notebook: Analyser les événements de manière interactive
4. Dans une CI/CD: Valider l'architecture événementielle automatiquement

DÉCOMMENTEZ LES EXEMPLES CI-DESSOUS POUR LES TESTER:
    """)

    # Example 1: Analyser les événements (sans serveur web)
    # Décommentez la ligne suivante pour tester:
    # example_analyze_events()

    # Example 2: Lancer un seul serveur dans un processus séparé
    # Décommentez les lignes suivantes pour tester:
    # process = example_launch_in_process()
    # input("Appuyez sur Entrée pour arrêter le serveur...")
    # process.terminate()
    # process.join()

    # Example 3: Lancer plusieurs serveurs en parallèle
    # Décommentez les lignes suivantes pour tester:
    # processes = example_launch_multiple_servers()
    # input("Appuyez sur Entrée pour arrêter tous les serveurs...")
    # for p in processes:
    #     p.terminate()
    #     p.join()

    print("\n💡 Éditez ce fichier pour décommenter les exemples que vous voulez tester.")
    print("   Ou consultez la documentation pour plus d'informations.\n")
