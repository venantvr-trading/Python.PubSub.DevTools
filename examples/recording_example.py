"""
Exemple complet : Enregistrement automatique des événements via IPC.

Ce fichier montre comment :
1. Démarrer DevTools pour recevoir les enregistrements
2. Démarrer l'application avec ServiceBus en mode recording
3. Les événements sont automatiquement enregistrés via HTTP
4. Arrêter proprement et sauvegarder le recording
"""
import multiprocessing
import time
from pathlib import Path

# ============================================================================
# ÉTAPE 1: DÉMARRER DEVTOOLS (dans un processus séparé)
# ============================================================================

def start_devtools():
    """Démarre le serveur DevTools Event Recorder."""
    from python_pubsub_devtools.config import EventRecorderConfig
    from python_pubsub_devtools.event_recorder.server import EventRecorderServer

    config = EventRecorderConfig(
        recordings_dir=Path("./recordings"),
        port=5556
    )

    server = EventRecorderServer(config)
    server.run(host='0.0.0.0', debug=False)


# ============================================================================
# ÉTAPE 2: DÉMARRER L'APPLICATION AVEC RECORDING ACTIVÉ
# ============================================================================

def run_trading_app_with_recording():
    """Exemple d'application qui publie des événements."""
    # IMPORTANT: Remplacez cette importation par votre ServiceBus réel
    # from your_app.service_bus import ServiceBusBase

    # Pour cet exemple, simulons avec un mock
    # Dans votre vraie application, utilisez votre ServiceBus
    from python_pubsub_client.base_bus import ServiceBusBase

    # Créer le ServiceBus avec recording activé
    service_bus = ServiceBusBase(
        url='ws://localhost:3000',
        consumer_name='TradingBot',
        enable_devtools=True,           # API pour replay (défaut: True)
        enable_recording=True,          # RECORDING AUTOMATIQUE
        recording_session_name='trading_session_example'
    )

    # Démarrer le ServiceBus
    service_bus.start()

    print("✅ ServiceBus started with recording enabled")
    print("   All published events will be automatically recorded to DevTools")
    print()

    # Simuler la publication d'événements
    try:
        for i in range(10):
            event_data = {
                'iteration': i,
                'timestamp': time.time(),
                'price': 100 + i * 0.5
            }

            service_bus.publish('TradeExecuted', event_data, 'TradingBot')
            print(f"   📨 Published event {i+1}/10: TradeExecuted")
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n⏸️  Interrupted by user")

    finally:
        # Arrêter proprement et sauvegarder le recording
        print("\n🛑 Stopping recording...")
        service_bus.stop_recording()
        service_bus.stop()
        print("✅ Recording saved to DevTools!")


# ============================================================================
# WORKFLOW COMPLET: DEVTOOLS + APPLICATION
# ============================================================================

def full_workflow():
    """Lance DevTools puis l'application avec recording."""

    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║            Event Recording - Workflow Automatique (IPC)                  ║
╚══════════════════════════════════════════════════════════════════════════╝

Ce workflow démontre l'enregistrement automatique cross-process :

1. DevTools démarre et écoute sur http://localhost:5556
2. L'application ServiceBus démarre avec enable_recording=True
3. Tous les événements publiés sont automatiquement envoyés à DevTools via HTTP
4. À l'arrêt, le recording est sauvegardé automatiquement

Aucun code supplémentaire nécessaire ! 🎉
""")

    # Démarrer DevTools dans un processus séparé
    print("🚀 Starting DevTools Event Recorder...")
    devtools_process = multiprocessing.Process(target=start_devtools, daemon=True)
    devtools_process.start()

    # Attendre que DevTools soit prêt
    print("   Waiting for DevTools to be ready...")
    time.sleep(3)
    print(f"✅ DevTools ready at http://localhost:5556\n")

    # Démarrer l'application avec recording
    print("🚀 Starting Trading Application with recording...")
    print()

    try:
        run_trading_app_with_recording()
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "="*80)
    print("🎬 Recording complete!")
    print(f"   View recordings at http://localhost:5556")
    print("="*80)

    # Laisser DevTools tourner pour visualiser
    input("\nPress Enter to stop DevTools and exit...")
    devtools_process.terminate()


# ============================================================================
# MODE MANUEL : CONTRÔLE TOTAL
# ============================================================================

def manual_recording_control():
    """Exemple avec contrôle manuel du recording."""
    from python_pubsub_devtools.event_recorder.server import EventRecorderServer
    from python_pubsub_devtools.config import EventRecorderConfig
    import requests

    # Démarrer DevTools
    config = EventRecorderConfig(recordings_dir=Path("./recordings"), port=5556)
    server = EventRecorderServer(config)

    def run_server():
        server.run(host='0.0.0.0', debug=False)

    process = multiprocessing.Process(target=run_server, daemon=True)
    process.start()
    time.sleep(2)

    print("✅ DevTools started\n")

    # Contrôle manuel via API
    print("📝 Manual recording control:")

    # 1. Démarrer une session
    response = requests.post('http://localhost:5556/api/record/start',
                            json={'session_name': 'manual_session'})
    print(f"   Start session: {response.json()}")

    # 2. Enregistrer quelques événements
    for i in range(5):
        requests.post('http://localhost:5556/api/record/event',
                     json={
                         'event_name': 'TestEvent',
                         'event_data': {'value': i},
                         'source': 'Manual'
                     })
        print(f"   Recorded event {i+1}/5")
        time.sleep(0.2)

    # 3. Arrêter et sauvegarder
    response = requests.post('http://localhost:5556/api/record/stop')
    result = response.json()
    print(f"   Stopped: {result['filename']} ({result['event_count']} events)\n")

    print(f"✅ Manual recording complete!")
    print(f"   View at http://localhost:5556")

    input("\nPress Enter to exit...")
    process.terminate()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--manual':
        # Mode manuel pour tests
        manual_recording_control()
    else:
        # Workflow complet automatique
        full_workflow()
