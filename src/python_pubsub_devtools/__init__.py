"""
PubSub Dev Tools - Comprehensive development and debugging tools for PubSub-based event-driven architectures

This library provides:
- Event Flow Visualization: Interactive diagrams of your event-driven architecture
- Event Recorder: Record and replay event streams for debugging
- Scenario Engine: Generic scenario-based testing with chaos engineering and assertions

Example:
    from python_pubsub_devtools.event_flow import EventFlowAnalyzer
    from python_pubsub_devtools.event_recorder import EventRecorder
    from python_pubsub_devtools.scenario_engine import ScenarioEngine, DataGenerator

    # Record events
    recorder = EventRecorder("my_session")
    recorder.start_recording(service_bus)

    # Analyze event flow
    analyzer = EventFlowAnalyzer()
    analyzer.analyze_events(events)

    # Run scenario testing
    engine = ScenarioEngine(generator=my_generator, service_bus=service_bus)
    engine.run_scenario(steps)
"""

__version__ = "0.2.0"
__author__ = "venantvr"

# Scenario Engine - import module, users import specific classes from it
from . import scenario_engine
# Event Flow
from .event_flow import EventFlowAnalyzer
# Event Recorder
from .event_recorder import EventRecorder, EventReplayer

__all__ = [
    # Version and metadata
    "__version__",
    "__author__",
    # Event Flow
    "EventFlowAnalyzer",
    # Event Recorder
    "EventRecorder",
    "EventReplayer",
    # Scenario Engine (module)
    "scenario_engine",
]
