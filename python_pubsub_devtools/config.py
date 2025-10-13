"""
Configuration management for PubSub Dev Tools

Provides dependency injection configuration for decoupling the tools from specific projects.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Set

import yaml


@dataclass
class EventFlowConfig:
    """Configuration for Event Flow Visualization"""

    agents_dir: Path
    events_dir: Path
    port: int = 5555
    test_agents: Set[str] = field(default_factory=set)
    namespace_colors: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure paths are Path objects"""
        self.agents_dir = Path(self.agents_dir)
        self.events_dir = Path(self.events_dir)

        # Default namespace colors
        if not self.namespace_colors:
            self.namespace_colors = {
                'bot_lifecycle': '#81c784',  # green
                'market_data': '#64b5f6',  # blue
                'indicator': '#9575cd',  # purple
                'internal': '#ba68c8',  # purple light
                'capital': '#ffd54f',  # yellow
                'pool': '#ffb74d',  # orange
                'position': '#ff8a65',  # deep orange
                'exchange': '#4dd0e1',  # cyan
                'command': '#a1887f',  # brown
                'database': '#90a4ae',  # blue grey
                'exit_strategy': '#aed581',  # light green
                'query': '#81d4fa',  # light blue
                'unknown': '#e0e0e0',  # grey
            }


@dataclass
class EventRecorderConfig:
    """Configuration for Event Recorder"""

    recordings_dir: Path
    port: int = 5556

    def __post_init__(self):
        """Ensure paths are Path objects and create directories"""
        self.recordings_dir = Path(self.recordings_dir)
        self.recordings_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class MockExchangeConfig:
    """Configuration for Mock Exchange"""

    port: int = 5557
    default_initial_price: float = 50000.0
    default_volatility: float = 0.02
    default_spread_bps: float = 10.0


@dataclass
class ScenarioTestingConfig:
    """Configuration for Scenario Testing"""

    scenarios_dir: Path
    reports_dir: Path
    port: int = 5558

    def __post_init__(self):
        """Ensure paths are Path objects and create directories"""
        self.scenarios_dir = Path(self.scenarios_dir)
        self.reports_dir = Path(self.reports_dir)
        self.scenarios_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class DevToolsConfig:
    """Main configuration for all PubSub Dev Tools"""

    event_flow: EventFlowConfig
    event_recorder: EventRecorderConfig
    mock_exchange: MockExchangeConfig
    scenario_testing: ScenarioTestingConfig

    @classmethod
    def from_yaml(cls, config_path: str | Path) -> "DevToolsConfig":
        """Load configuration from YAML file

        Args:
            config_path: Path to YAML configuration file

        Returns:
            DevToolsConfig instance

        Example YAML structure:
            agents_dir: "path/to/agents"
            events_dir: "path/to/events"
            recordings_dir: "recordings"
            scenarios_dir: "scenarios"
            reports_dir: "reports"

            event_flow:
              port: 5555
              test_agents:
                - "token_balance_refresh"
              namespace_colors:
                bot_lifecycle: "#81c784"

            event_recorder:
              port: 5556

            mock_exchange:
              port: 5557

            scenario_testing:
              port: 5558
        """
        with open(config_path) as f:
            data = yaml.safe_load(f)

        # Extract common paths
        agents_dir = data.get('agents_dir', 'agents')
        events_dir = data.get('events_dir', 'events')
        recordings_dir = data.get('recordings_dir', 'recordings')
        scenarios_dir = data.get('scenarios_dir', 'scenarios')
        reports_dir = data.get('reports_dir', 'reports')

        # Event Flow config
        event_flow_data = data.get('event_flow', {})
        event_flow = EventFlowConfig(
            agents_dir=agents_dir,
            events_dir=events_dir,
            port=event_flow_data.get('port', 5555),
            test_agents=set(event_flow_data.get('test_agents', [])),
            namespace_colors=event_flow_data.get('namespace_colors', {})
        )

        # Event Recorder config
        event_recorder_data = data.get('event_recorder', {})
        event_recorder = EventRecorderConfig(
            recordings_dir=recordings_dir,
            port=event_recorder_data.get('port', 5556)
        )

        # Mock Exchange config
        mock_exchange_data = data.get('mock_exchange', {})
        mock_exchange = MockExchangeConfig(
            port=mock_exchange_data.get('port', 5557),
            default_initial_price=mock_exchange_data.get('default_initial_price', 50000.0),
            default_volatility=mock_exchange_data.get('default_volatility', 0.02),
            default_spread_bps=mock_exchange_data.get('default_spread_bps', 10.0)
        )

        # Scenario Testing config
        scenario_testing_data = data.get('scenario_testing', {})
        scenario_testing = ScenarioTestingConfig(
            scenarios_dir=scenarios_dir,
            reports_dir=reports_dir,
            port=scenario_testing_data.get('port', 5558)
        )

        return cls(
            event_flow=event_flow,
            event_recorder=event_recorder,
            mock_exchange=mock_exchange,
            scenario_testing=scenario_testing
        )

    @classmethod
    def from_dict(cls, config_dict: Dict) -> "DevToolsConfig":
        """Create configuration from dictionary

        Args:
            config_dict: Configuration dictionary

        Returns:
            DevToolsConfig instance
        """
        # Event Flow
        event_flow = EventFlowConfig(
            agents_dir=config_dict['agents_dir'],
            events_dir=config_dict['events_dir'],
            port=config_dict.get('event_flow_port', 5555),
            test_agents=set(config_dict.get('test_agents', [])),
            namespace_colors=config_dict.get('namespace_colors', {})
        )

        # Event Recorder
        event_recorder = EventRecorderConfig(
            recordings_dir=config_dict.get('recordings_dir', 'recordings'),
            port=config_dict.get('event_recorder_port', 5556)
        )

        # Mock Exchange
        mock_exchange = MockExchangeConfig(
            port=config_dict.get('mock_exchange_port', 5557)
        )

        # Scenario Testing
        scenario_testing = ScenarioTestingConfig(
            scenarios_dir=config_dict.get('scenarios_dir', 'scenarios'),
            reports_dir=config_dict.get('reports_dir', 'reports'),
            port=config_dict.get('scenario_testing_port', 5558)
        )

        return cls(
            event_flow=event_flow,
            event_recorder=event_recorder,
            mock_exchange=mock_exchange,
            scenario_testing=scenario_testing
        )

    def to_yaml(self, output_path: str | Path) -> None:
        """Save configuration to YAML file

        Args:
            output_path: Path to output YAML file
        """
        data = {
            'agents_dir': str(self.event_flow.agents_dir),
            'events_dir': str(self.event_flow.events_dir),
            'recordings_dir': str(self.event_recorder.recordings_dir),
            'scenarios_dir': str(self.scenario_testing.scenarios_dir),
            'reports_dir': str(self.scenario_testing.reports_dir),
            'event_flow': {
                'port': self.event_flow.port,
                'test_agents': list(self.event_flow.test_agents),
                'namespace_colors': self.event_flow.namespace_colors
            },
            'event_recorder': {
                'port': self.event_recorder.port
            },
            'mock_exchange': {
                'port': self.mock_exchange.port,
                'default_initial_price': self.mock_exchange.default_initial_price,
                'default_volatility': self.mock_exchange.default_volatility,
                'default_spread_bps': self.mock_exchange.default_spread_bps
            },
            'scenario_testing': {
                'port': self.scenario_testing.port
            }
        }

        with open(output_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
