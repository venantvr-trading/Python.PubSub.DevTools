"""
Scenario Schema - Pydantic models for declarative scenario testing.

Defines the structure for test scenarios loaded from YAML files.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChaosType(str, Enum):
    """Type of chaos action to inject"""
    DELAY = "delay"
    DROP = "drop"
    FAILURE = "failure"
    LATENCY = "latency"


class ChaosAction(BaseModel):
    """
    Chaos engineering action to inject during scenario execution.

    Attributes:
        type: Type of chaos (delay, drop, failure, latency)
        target_event: Event name to target (supports wildcards)
        duration_ms: Duration of chaos in milliseconds
        probability: Probability of chaos (0.0-1.0), default 1.0
        delay_ms: Delay in ms (for delay/latency types)
        error_message: Custom error message (for failure type)
    """
    type: ChaosType
    target_event: str = Field(..., description="Event name to target (supports wildcards)")
    duration_ms: int = Field(default=0, description="Duration of chaos in ms (0 = entire scenario)")
    probability: float = Field(default=1.0, ge=0.0, le=1.0, description="Probability of chaos")
    delay_ms: Optional[int] = Field(default=None, description="Delay in ms (for delay/latency)")
    error_message: Optional[str] = Field(default=None, description="Error message (for failure)")


class AssertionType(str, Enum):
    """Type of assertion to check"""
    EVENT_COUNT = "event_count"
    EVENT_VALUE = "event_value"
    NO_EVENT = "no_event"


class Assertion(BaseModel):
    """
    Assertion to validate scenario behavior.

    Attributes:
        type: Type of assertion (event_count, event_value, no_event)
        event_name: Event name to check
        expected_count: Expected event count (for event_count)
        field_path: Dot-separated path to field (for event_value)
        expected_value: Expected value (for event_value)
        operator: Comparison operator (==, !=, >, <, >=, <=, contains)
    """
    type: AssertionType
    event_name: str
    expected_count: Optional[int] = None
    field_path: Optional[str] = None
    expected_value: Optional[Any] = None
    operator: str = "=="
    description: Optional[str] = None


class TestScenario(BaseModel):
    """
    Declarative test scenario with chaos engineering and assertions.

    Example YAML:
        name: "Market Crash Test"
        description: "Test bot behavior during market crash"
        timeout_ms: 30000
        initial_events:
          - event_name: "MarketDataReceived"
            event_data:
              symbol: "BTC/USDT"
              price: 50000
        chaos:
          - type: "failure"
            target_event: "ExchangeOrderPlaced"
            probability: 0.5
        assertions:
          - type: "event_count"
            event_name: "PositionClosed"
            expected_count: 1
    """
    name: str = Field(..., description="Scenario name")
    description: Optional[str] = Field(default=None, description="Scenario description")
    timeout_ms: int = Field(default=30000, description="Scenario timeout in ms")

    initial_events: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Initial events to publish"
    )

    chaos: List[ChaosAction] = Field(
        default_factory=list,
        description="Chaos actions to inject"
    )

    assertions: List[Assertion] = Field(
        default_factory=list,
        description="Assertions to validate"
    )

    tags: List[str] = Field(
        default_factory=list,
        description="Tags for filtering scenarios"
    )

    @classmethod
    def from_yaml_file(cls, file_path: str) -> TestScenario:
        """
        Load a scenario from a YAML file.

        Args:
            file_path: Path to YAML file

        Returns:
            TestScenario instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If YAML is invalid
        """
        from pathlib import Path
        import yaml

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Scenario file not found: {file_path}")

        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError(f"Empty or invalid YAML file: {file_path}")

        return cls(**data)
