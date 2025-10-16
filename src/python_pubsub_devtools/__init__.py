"""
PubSub DevTools - Outils de développement pour architectures événementielles PubSub.

Cette bibliothèque fournit :
- Event Flow Visualization: Diagrammes interactifs de votre architecture événementielle
- Event Recorder: Enregistrement et rejeu de flux d'événements
- Mock Exchange: Simulateur de marché pour tests
- Scenario Testing: Tests de scénarios avec chaos engineering

Example (CLI):
    $ pubsub-tools serve-all --config devtools_config.yaml

Example (API programmatique):
    from python_pubsub_devtools.config import DevToolsConfig
    from python_pubsub_devtools.event_flow.server import EventFlowServer

    config = DevToolsConfig.from_yaml("devtools_config.yaml")
    server = EventFlowServer(config.event_flow)
    server.run()  # Bloquant
"""

__version__ = "0.2.0"
__author__ = "venantvr"

# Configuration
from .config import (
    DevToolsConfig,
    EventFlowConfig,
    EventRecorderConfig,
    MockExchangeConfig,
    ScenarioTestingConfig,
)

# Event Flow - Analyse et visualisation
from .event_flow import EventFlowAnalyzer

# Event Recorder - Enregistrement et rejeu
from .event_recorder import EventRecorder, EventReplayer

__all__ = [
    # Version et métadonnées
    "__version__",
    "__author__",
    # Configuration
    "DevToolsConfig",
    "EventFlowConfig",
    "EventRecorderConfig",
    "MockExchangeConfig",
    "ScenarioTestingConfig",
    # Event Flow
    "EventFlowAnalyzer",
    # Event Recorder
    "EventRecorder",
    "EventReplayer",
]
