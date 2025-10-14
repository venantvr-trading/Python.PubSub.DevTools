"""
Configuration for PubSub DevTools services
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class EventFlowConfig:
    """Configuration for Event Flow Visualization service"""
    agents_dir: Path
    events_dir: Path
    port: int = 5555
    test_agents: List[str] = field(default_factory=list)
    namespace_colors: Dict[str, str] = field(default_factory=lambda: {
        'trading': '#4caf50',
        'risk': '#ff9800',
        'monitoring': '#2196f3',
        'commands': '#9c27b0',
        'execution': '#f44336',
        'unknown': '#e0e0e0'
    })


@dataclass
class EventRecorderConfig:
    """Configuration for Event Recorder service"""
    recordings_dir: Path
    port: int = 5556


@dataclass
class DevToolsConfig:
    """Main configuration for all DevTools services"""
    agents_dir: Path
    events_dir: Path
    recordings_dir: Path
    event_flow_port: int = 5555
    event_recorder_port: int = 5556
    test_agents: List[str] = field(default_factory=list)

    def get_event_flow_config(self) -> EventFlowConfig:
        """Get Event Flow configuration"""
        return EventFlowConfig(
            agents_dir=self.agents_dir,
            events_dir=self.events_dir,
            port=self.event_flow_port,
            test_agents=self.test_agents
        )

    def get_event_recorder_config(self) -> EventRecorderConfig:
        """Get Event Recorder configuration"""
        return EventRecorderConfig(
            recordings_dir=self.recordings_dir,
            port=self.event_recorder_port
        )
