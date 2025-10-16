# PubSub DevTools

**Une suite complète d'outils de développement et de débogage pour architectures événementielles basées sur PubSub.**

Cette bibliothèque est conçue comme un **outil d'aide au développement** avec une API programmatique prioritaire. Les développeurs peuvent facilement instancier et lancer
les serveurs directement depuis leur propre code (scripts de test, sessions de débogage, IDE) tout en bénéficiant d'une CLI pratique pour une utilisation autonome.

## 🎯 Fonctionnalités

### 📊 Event Flow Visualization

- Diagrammes interactifs de flux d'événements
- Vues hiérarchiques et graphes complets
- Filtrage par namespace avec codage couleur
- Filtrage des événements échoués/rejetés
- Support du mode sombre
- Rendu professionnel avec GraphViz

### 🎬 Event Recorder & Replayer

- Enregistrement de flux d'événements avec timestamps
- Tableau de bord web pour parcourir les sessions
- Filtrage et analyse des séquences d'événements
- Statistiques détaillées par enregistrement
- Analyse de fréquence des événements

### 🎰 Mock Exchange Simulator

- Simulation de marché en temps réel
- Scénarios multiples (tendance, volatilité, crash)
- Configuration de prix initial, volatilité et spread
- Visualisation interactive des prix

### 🎯 Scenario Testing Framework

- Moteur de scénarios agnostique au domaine
- Génération de données avec profils configurables
- Ingénierie du chaos (délais, échecs, corruption)
- Vérification automatique d'assertions
- Support multi-phases
- Rapports de tests complets

## Installation

```bash
pip install python_pubsub_devtools
```

Or install from source:

```bash
git clone <repository>
cd Python.PubSub.DevTools
pip install -e .
```

## 🚀 Démarrage Rapide

### 1. Configuration

Créez un fichier `devtools_config.yaml` à la racine de votre projet :

```bash
# Générer un fichier de configuration exemple
pubsub-tools config-example -o devtools_config.yaml
```

Puis éditez le fichier pour ajuster les chemins :

```yaml
# Configuration PubSub DevTools
agents_dir: "./agents"
events_dir: "./events"
recordings_dir: "./recordings"
scenarios_dir: "./scenarios"
reports_dir: "./reports"

event_flow:
  port: 5555

event_recorder:
  port: 5556

mock_exchange:
  port: 5557

scenario_testing:
  port: 5558
```

### 2. Utilisation CLI

```bash
# Lancer un service spécifique
pubsub-tools event-flow --config devtools_config.yaml
pubsub-tools event-recorder --config devtools_config.yaml
pubsub-tools mock-exchange --config devtools_config.yaml
pubsub-tools scenario-testing --config devtools_config.yaml

# Lancer tous les services simultanément
pubsub-tools serve-all --config devtools_config.yaml
```

**Services disponibles :**

| Service          | Port | Description                          |
|------------------|------|--------------------------------------|
| Event Flow       | 5555 | Visualisation des flux d'événements  |
| Event Recorder   | 5556 | Enregistrement et rejeu d'événements |
| Mock Exchange    | 5557 | Simulateur de marché                 |
| Scenario Testing | 5558 | Tests de scénarios avec chaos        |

### 3. Utilisation Programmatique (Recommandé)

L'API programmatique est l'interface principale pour intégrer les outils dans vos scripts, tests ou IDE :

```python
from python_pubsub_devtools.config import DevToolsConfig
from python_pubsub_devtools.event_flow.server import EventFlowServer

# Charger la configuration depuis un fichier YAML
config = DevToolsConfig.from_yaml("devtools_config.yaml")

# Instancier et lancer un serveur (bloquant)
server = EventFlowServer(config.event_flow)
server.run()
```

**Lancer plusieurs serveurs en parallèle :**

```python
import multiprocessing
from python_pubsub_devtools.config import DevToolsConfig
from python_pubsub_devtools.event_flow.server import EventFlowServer
from python_pubsub_devtools.event_recorder.server import EventRecorderServer

config = DevToolsConfig.from_yaml("devtools_config.yaml")

def run_event_flow():
    server = EventFlowServer(config.event_flow)
    server.run(host='0.0.0.0', debug=False)

def run_event_recorder():
    server = EventRecorderServer(config.event_recorder)
    server.run(host='0.0.0.0', debug=False)

# Lancer dans des processus séparés
processes = [
    multiprocessing.Process(target=run_event_flow),
    multiprocessing.Process(target=run_event_recorder),
]

for p in processes:
    p.start()
```

Voir `examples/basic_usage.py` pour plus d'exemples.

## Features Overview

### Event Flow Visualization

Visualize the complete event-driven architecture:

- **Publishers & Subscribers**: See who publishes and subscribes to which events
- **Event Namespaces**: Organize events by namespace with color coding
- **Interactive Diagrams**: Hierarchical tree and complete graph views
- **Filtering**: Filter by namespace, hide failed/rejected events
- **Dark Mode**: Comfortable visualization in any lighting condition
- **GraphViz Layout**: Professional-quality diagram rendering

### Event Recorder

Record and replay event streams for:

- **Debugging**: Analyze complex event sequences
- **Test Fixtures**: Create reproducible test scenarios
- **Performance Analysis**: Track event timing and frequency
- **Session Management**: Browse and compare multiple recordings
- **Statistics**: Event counts, duration, frequency analysis

### Generic Scenario Testing

Build domain-agnostic scenario tests:

- **Data Generation**: Pluggable data generators for any domain
- **Scenario Profiles**: Bull/bear markets, load patterns, failure modes, etc.
- **Chaos Engineering**: Inject delays, failures, data corruption
- **Assertions**: Built-in and custom assertion checkers
- **Multi-Phase**: Complex scenarios with multiple phases
- **Reporting**: Comprehensive test reports with statistics

## 🏗️ Architecture

La bibliothèque suit une architecture modulaire avec configuration centralisée :

```
python_pubsub_devtools/
├── config.py                    # Configuration Pydantic centralisée avec support YAML
├── cli/                         # Interface en ligne de commande unifiée
│   └── main.py                  # Commandes CLI avec Click
├── event_flow/                  # Visualisation des flux d'événements
│   ├── __init__.py             # API publique (EventFlowAnalyzer, EventFlowServer)
│   ├── server.py               # Serveur Flask (Application Factory)
│   ├── views.py                # Routes Flask
│   └── analyze_event_flow.py  # Logique métier d'analyse
├── event_recorder/              # Enregistrement et rejeu d'événements
│   ├── __init__.py             # API publique (EventRecorder, EventRecorderServer)
│   ├── server.py               # Serveur Flask (Application Factory)
│   ├── views.py                # Routes Flask
│   └── event_recorder.py       # Logique métier d'enregistrement
├── mock_exchange/               # Simulateur de marché
│   ├── __init__.py             # API publique (MockExchangeServer)
│   ├── server.py               # Serveur Flask (Application Factory)
│   ├── views.py                # Routes Flask
│   └── scenario_exchange.py    # Moteur de simulation
├── scenario_testing/            # Tests de scénarios avec chaos
│   ├── __init__.py             # API publique (ScenarioTestingServer)
│   ├── server.py               # Serveur Flask (Application Factory)
│   ├── views.py                # Routes Flask
│   ├── scenario_runner.py      # Moteur de scénarios
│   ├── assertion_checker.py    # Système d'assertions
│   └── chaos_injector.py       # Ingénierie du chaos
└── web/                         # Assets web partagés
    ├── templates/              # Templates HTML Jinja2
    └── static/                 # CSS, JavaScript, images
```

### Principes de conception

1. **API programmatique prioritaire** : Classes `...Server` stables pour intégration facile
2. **Application Factory Pattern** : Chaque service expose une fonction `create_app(config)`
3. **Configuration centralisée** : Fichier YAML unique avec validation Pydantic
4. **Séparation des préoccupations** : Logique métier, routes Flask et serveurs séparés
5. **Chemins relatifs intelligents** : Résolution automatique par rapport au fichier de config

## Dependencies

- Flask >= 2.0.0 (Web interface)
- Click >= 8.0.0 (CLI)
- pydot >= 1.4.0 (Event flow diagrams)
- pandas >= 2.0.0 (Data analysis)
- matplotlib >= 3.5.0 (Visualization)
- networkx >= 2.8.0 (Graph analysis)
- PyYAML >= 6.0 (Configuration)
- Pydantic >= 2.0 (Data validation)

## Development

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Run linters
flake8 python_pubsub_devtools
mypy python_pubsub_devtools
```

## License

MIT License
