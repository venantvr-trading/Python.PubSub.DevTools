"""
PubSub Dev Tools - Comprehensive development and debugging tools for PubSub-based event-driven architectures

This library provides:
- Event Flow Visualization: Interactive diagrams of your event-driven architecture
- Event Recorder: Record and replay event streams for debugging

Example:
    from python_pubsub_devtools.event_flow import EventFlowAnalyzer
    from python_pubsub_devtools.event_recorder import EventRecorder

    # Record events
    recorder = EventRecorder("my_session")
    recorder.start_recording(service_bus)

    # Analyze event flow
    analyzer = EventFlowAnalyzer()
    analyzer.analyze_events(events)
"""

__version__ = "0.1.0"
__author__ = "venantvr"

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
]
