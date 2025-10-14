"""
Basic usage example for PubSub Dev Tools

This demonstrates how to use the library programmatically.
"""
from pathlib import Path

from python_pubsub_devtools import DevToolsConfig

# Method 1: Load from YAML config file
config = DevToolsConfig.from_yaml("devtools_config.yaml")

# Method 2: Create from dictionary
config_dict = {
    'agents_dir': 'python_pubsub_risk/agents',
    'events_dir': 'python_pubsub_risk/events',
    'recordings_dir': 'recordings',
    'scenarios_dir': 'scenarios',
    'reports_dir': 'reports',
    'event_flow_port': 5555,
    'event_recorder_port': 5556,
    'mock_exchange_port': 5557,
    'scenario_testing_port': 5558,
}
config = DevToolsConfig.from_dict(config_dict)

# Access individual configurations
print(f"Event Flow agents directory: {config.event_flow.agents_dir}")
print(f"Event Recorder port: {config.event_recorder.port}")
print(f"Mock Exchange port: {config.mock_exchange.port}")
print(f"Scenario Testing port: {config.scenario_testing.port}")

# Use Event Flow Analyzer
from python_pubsub_devtools.event_flow import EventFlowAnalyzer

analyzer = EventFlowAnalyzer(config.event_flow.agents_dir)
analyzer.analyze()

events = analyzer.get_all_events()
print(f"\nFound {len(events)} events in the system")

# Print summary
analyzer.print_summary()

# Generate Graphviz diagram
dot_content = analyzer.generate_graphviz()
Path("event_flow.dot").write_text(dot_content)
print("\nEvent flow diagram saved to event_flow.dot")
print("Generate image with: dot -Tpng event_flow.dot -o event_flow.png")