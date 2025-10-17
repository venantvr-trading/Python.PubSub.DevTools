# Event Recorder & Replayer - Time-Traveling Debugging 🎬

Un système d'enregistrement et de rejeu d'événements pour debug, test et reproduction de bugs.

## 🎯 Concept

Le Event Recorder/Replayer permet de :

- **Enregistrer** tous les événements d'une session de trading
- **Sauvegarder** les événements avec leur timing exact
- **Rejouer** la session à n'importe quelle vitesse (0.1x à 100x)
- **Filtrer** les événements lors du rejeu
- **Analyser** les patterns d'événements

## 📦 Installation

Aucune installation requise - les fichiers sont dans `tools/` :

- `event_recorder.py` - Classes principales
- `example_recorder_usage.py` - Exemples d'utilisation
- `recordings/` - Répertoire des enregistrements

## 🚀 Usage Rapide

### Enregistrer une session

```python
from event_recorder import EventRecorder

# Créer un recorder
recorder = EventRecorder("ma_session")

# Commencer l'enregistrement
recorder.start_recording(service_bus)

# ... le bot tourne et publie des événements ...

# Arrêter et sauvegarder
recorder.stop_recording()
filepath = recorder.save()
```

### Rejouer une session

```python
from event_recorder import EventReplayer

# Charger l'enregistrement
replayer = EventReplayer("recordings/ma_session_20251012_120000.json")

# Rejouer à vitesse normale
replayer.replay(service_bus, speed_multiplier=1.0)

# Rejouer 10x plus rapide
replayer.replay(service_bus, speed_multiplier=10.0)
```

## 📋 Exemples Complets

### Exemple 1 : Enregistrer avec Context Manager

```python
with EventRecorder("debug_session") as recorder:
    recorder.start_recording(service_bus)

    # Démarrer le bot
    orchestrator.start_workflow()
    time.sleep(60)  # Laisser tourner 1 minute
    orchestrator.stop()

    # Sauvegarder automatiquement
    recorder.save()
# L'enregistrement s'arrête automatiquement en sortant du with
```

### Exemple 2 : Rejouer avec Filtrage

```python
replayer = EventReplayer("recordings/session.json")

# Ne rejouer que les événements Failed
replayer.replay(
    service_bus,
    speed_multiplier=10.0,
    event_filter=lambda name: "Failed" in name
)

# Ne rejouer que les achats/ventes
replayer.replay(
    service_bus,
    speed_multiplier=1.0,
    event_filter=lambda name: name in ["PositionPurchased", "PositionSold"]
)
```

### Exemple 3 : Analyser sans Rejouer

```python
replayer = EventReplayer("recordings/session.json")

# Obtenir le résumé des événements
summary = replayer.get_event_summary()
for event_name, count in summary.items():
    print(f"{event_name}: {count}x")

# Afficher la timeline
replayer.print_timeline(max_events=50)
```

### Exemple 4 : Progress Callback

```python
def show_progress(current, total):
    percent = (current / total) * 100
    print(f"\rReplay progress: {percent:.1f}%", end="", flush=True)

replayer.replay(
    service_bus,
    speed_multiplier=10.0,
    progress_callback=show_progress
)
```

## 🔧 CLI Interface

Le recorder dispose d'une interface CLI pour analyser les enregistrements :

```bash
# Afficher les informations d'un enregistrement
python event_recorder.py info recordings/session.json

# Afficher la timeline
python event_recorder.py timeline recordings/session.json --max-events 100

# Rejouer (nécessite du code Python)
# Voir example_recorder_usage.py
```

## 📊 Format d'Enregistrement

Les enregistrements sont sauvegardés en JSON :

```json
{
  "session_name": "bull_run_scenario",
  "start_time": "2025-10-12T10:00:00+00:00",
  "duration_ms": 45000,
  "total_events": 127,
  "events": [
    {
      "timestamp_offset_ms": 0,
      "event_name": "BotMonitoringCycleStarted",
      "event_data": {
        "cycle_number": 1,
        "timestamp": "2025-10-12T10:00:00+00:00"
      },
      "source": "Orchestrator"
    },
    {
      "timestamp_offset_ms": 523,
      "event_name": "MarketPriceFetched",
      "event_data": {
        "cycle_id": 1,
        "current_price": "50000.0",
        ...
      },
      "source": "MarketPriceFetcher"
    }
  ]
}
```

## 🎯 Cas d'Usage

### 1. Reproduire un Bug

```python
# 1. En production, détecter un bug
if detect_bug():
    recorder = EventRecorder("bug_reproduction")
    recorder.start_recording(service_bus)
    # Continuer l'exécution jusqu'à la fin du cycle
    recorder.save()

# 2. En dev, rejouer exactement le même scénario
replayer = EventReplayer("recordings/bug_reproduction_xxx.json")
replayer.replay(service_bus, speed_multiplier=1.0)
# Le bug se reproduit à l'identique !
```

### 2. Tests de Régression

```python
# Enregistrer une session de référence
recorder = EventRecorder("regression_baseline")
recorder.start_recording(service_bus)
run_trading_cycle()
baseline_file = recorder.save()

# Plus tard, après modifications du code
replayer = EventReplayer(baseline_file)
replayer.replay(service_bus, speed_multiplier=100.0)
# Vérifier que le comportement est identique
```

### 3. Tests de Performance

```python
# Enregistrer une session
recorder = EventRecorder("perf_test")
recorder.start_recording(service_bus)
run_100_cycles()
recording = recorder.save()

# Rejouer à différentes vitesses pour tester les limites
for speed in [1, 10, 50, 100]:
    start = time.time()
    replayer.replay(service_bus, speed_multiplier=speed)
    duration = time.time() - start
    print(f"Speed {speed}x: {duration:.2f}s")
```

### 4. Analyser un Échec

```python
replayer = EventReplayer("recordings/failed_session.json")

# Compter les échecs
summary = replayer.get_event_summary()
failed_count = sum(count for event, count in summary.items() if "Failed" in event)
print(f"Total failures: {failed_count}")

# Voir la timeline des échecs
replayer_filtered = replayer.filter_events(lambda name: "Failed" in name)
replayer_filtered.print_timeline()
```

## 🔬 Fonctionnalités Avancées

### Créer un Enregistrement Filtré

```python
replayer = EventReplayer("recordings/full_session.json")

# Créer un nouveau replayer avec seulement les événements de buy
buy_replayer = replayer.filter_events(
    lambda name: "Buy" in name or "Purchase" in name
)

# Rejouer seulement les achats
buy_replayer.replay(service_bus, speed_multiplier=10.0)
```

### Inspecter les Données d'Événement

```python
replayer = EventReplayer("recordings/session.json")

for event_data in replayer.events:
    event_name = event_data["event_name"]
    timestamp = event_data["timestamp_offset_ms"]
    data = event_data["event_data"]

    if event_name == "PositionPurchased":
        print(f"Purchase at {timestamp}ms: {data['purchase_price']} {data['pair']}")
```

## 📈 Statistiques

```python
replayer = EventReplayer("recordings/session.json")

print(f"Session: {replayer.session_name}")
print(f"Duration: {replayer.duration_ms / 1000:.2f}s")
print(f"Total events: {len(replayer.events)}")

summary = replayer.get_event_summary()
print("\nTop 5 most frequent events:")
for event_name, count in list(summary.items())[:5]:
    print(f"  {event_name}: {count}x")
```

## ⚠️ Limitations

1. **Taille des enregistrements** : Les sessions longues peuvent générer de gros fichiers JSON
2. **Sérialisation** : Certains objets complexes peuvent ne pas se sérialiser correctement
3. **Effets de bord** : Le rejeu publie des événements réels - attention aux effets de bord (DB, exchange)
4. **Timestamps relatifs** : Les timestamps sont relatifs au début de l'enregistrement, pas absolus

## 💡 Best Practices

1. **Nommer les sessions** : Utilisez des noms descriptifs (`bug_234_flash_crash`, `perf_test_baseline`)
2. **Nettoyer régulièrement** : Les enregistrements s'accumulent dans `recordings/`
3. **Filtrer lors du rejeu** : Utilisez `event_filter` pour accélérer les tests ciblés
4. **Vitesse élevée** : Utilisez `speed_multiplier=100.0` pour les tests rapides
5. **Context manager** : Utilisez `with EventRecorder()` pour cleanup automatique

## 🧪 Tests

Les tests sont dans `tests/tools/test_event_recorder.py` :

```bash
# Lancer les tests
python -m pytest tests/tools/test_event_recorder.py -v

# Tester seulement le recorder
python -m pytest tests/tools/test_event_recorder.py::TestEventRecorder -v

# Tester seulement le replayer
python -m pytest tests/tools/test_event_recorder.py::TestEventReplayer -v
```

## 📚 Exemples Complets

Voir `example_recorder_usage.py` pour des exemples complets et exécutables :

```bash
python tools/example_recorder_usage.py
```

## 🎓 Architecture

### EventRecorder

- Intercepte `service_bus.publish()`
- Enregistre tous les événements avec timestamp relatif
- Sérialise les données d'événement (Pydantic → dict)
- Sauvegarde en JSON

### EventReplayer

- Charge un fichier JSON d'enregistrement
- Désérialise les événements (dict → Pydantic)
- Rejoue avec timing préservé (ajustable via `speed_multiplier`)
- Supporte le filtrage et l'analyse

## 🌐 Web Dashboard

Un dashboard web interactif est disponible pour visualiser et analyser les recordings :

```bash
# Lancer le dashboard
python tools/event_recorder/serve_recorder.py

# Ouvrir dans le navigateur
open http://localhost:5556
```

**Fonctionnalités du dashboard** :

- 📋 **Liste des recordings** : Vue d'ensemble avec métadonnées (durée, événements, date)
- 📊 **Statistiques globales** : Total events, durée totale, moyenne par recording
- 🔍 **Vue détaillée** : Timeline complète des événements de chaque recording
- 📝 **Sélection et Création** : Sélectionnez des événements dans la timeline pour créer un nouvel enregistrement filtré.
- 📈 **Graphiques** : Distribution des événements par type (bar charts)
- 🔎 **Filtrage** : Recherche en temps réel dans la timeline
- 🎮 **Contrôles de replay (Simulation)** : Interface pour simuler un replay dans le navigateur (Play/Pause/Vitesse).
- 🔗 **Navigation** : Liens vers les autres outils (Event Flow, Mock Exchange, Testing)

**API REST** :

- `GET /` : Page principale avec liste des recordings
- `GET /recording/<filename>` : Vue détaillée d'un recording
- `GET /api/recordings` : JSON avec metadata de tous les recordings
- `GET /api/recording/<filename>` : JSON complet d'un recording
- `POST /api/record/start` : Démarre une session d'enregistrement à distance.
- `POST /api/record/event` : Enregistre un événement dans la session active.
- `POST /api/record/stop` : Arrête et sauvegarde la session.
- `POST /api/replay/start/<filename>` : Démarre une simulation de replay pour l'UI.

**Intégration** :

- Même charte graphique que Event Flow Visualization
- Port 5556 (Event Flow: 5555, Mock Exchange: 5557, Testing: 5558)
- Support des deux formats de recordings (ancien et nouveau)

## 🚧 Future Enhancements

Idées pour améliorer l'outil :

- Compression des enregistrements (gzip)
- Support SQLite pour gros enregistrements
- ✅ ~~UI web pour visualiser les recordings~~ (Fait!)
- Merge de plusieurs recordings
- Export en différents formats (CSV, Parquet)
- Replay controls dans le web UI (play/pause/speed)
- Comparaison de 2 recordings côte à côte