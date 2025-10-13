"""
PubSub Dev Tools - Comprehensive development and debugging tools for PubSub-based event-driven architectures

This library provides:
- Event Flow Visualization: Interactive diagrams of your event-driven architecture
- Event Recorder: Record and replay event streams
- Mock Exchange: Simulate market scenarios for testing
- Scenario Testing: YAML-based scenario testing with chaos injection
- Metrics Collection: Collect and analyze event metrics

Example:
    from python_pubsub_devtools import DevToolsConfig
    from python_pubsub_devtools.event_flow.server import EventFlowServer

    config = DevToolsConfig.from_yaml("devtools_config.yaml")
    server = EventFlowServer(config.event_flow)
    server.run()
"""

__version__ = "0.1.0"
__author__ = "venantvr"

# Core configuration
from .config import (
    DevToolsConfig,
    EventFlowConfig,
    EventRecorderConfig,
    MockExchangeConfig,
    ScenarioTestingConfig,
)
# Event Flow
from .event_flow import EventFlowAnalyzer
# Event Recorder
from .event_recorder import EventRecorder, EventReplayer
# Metrics
from .metrics import (
    EventMetricsCollector,
    Counter,
    Histogram,
    get_metrics_collector,
    collect_metrics,
)
# Mock Exchange
from .mock_exchange import ScenarioBasedMockExchange, MarketScenario
# Scenario Testing
from .scenario_testing import (
    ScenarioRunner,
    ChaosInjector,
    AssertionChecker,
    TestScenario,
    ChaosAction,
)

__all__ = [
    # Version and metadata
    "__version__",
    # Core configuration
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
    # Mock Exchange
    "ScenarioBasedMockExchange",
    "MarketScenario",
    # Scenario Testing
    "ScenarioRunner",
    "ChaosInjector",
    "AssertionChecker",
    "TestScenario",
    "ChaosAction",
    # Metrics
    "EventMetricsCollector",
    "Counter",
    "Histogram",
    "get_metrics_collector",
    "collect_metrics",
]
