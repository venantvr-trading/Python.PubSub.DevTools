"""
Scenario Testing Framework - Schema Definitions

Defines the structure of declarative test scenarios using Pydantic.
"""
from typing import Optional, Dict, Any, List, Union, Literal

from pydantic import BaseModel, Field, ConfigDict


class ExchangeSetup(BaseModel):
    """Exchange configuration for scenario"""
    scenario: str = Field(description="Market scenario name (bull_run, flash_crash, etc.)")
    initial_price: float = Field(default=50000.0, description="Initial price")
    pair: str = Field(default="BTC/USDT", description="Trading pair")
    volatility_multiplier: float = Field(default=1.0, description="Volatility multiplier")
    spread_bps: int = Field(default=20, description="Spread in basis points")


class BotSetup(BaseModel):
    """Bot configuration for scenario"""
    initial_capital: float = Field(default=10000.0, description="Initial capital in USDT")
    pool_count: int = Field(default=5, description="Number of pools")
    poll_interval: int = Field(default=60, description="Poll interval in seconds")


class RecordingSetup(BaseModel):
    """Event recording configuration"""
    enabled: bool = Field(default=True, description="Enable event recording")
    output: str = Field(default="recordings/{scenario_name}.json", description="Output file path")


class ReportSetup(BaseModel):
    """Test report configuration"""
    format: Literal["json", "html", "markdown"] = Field(default="html", description="Report format")
    output: str = Field(default="reports/{scenario_name}.html", description="Output file path")
    include_events: bool = Field(default=True, description="Include event timeline in report")
    include_statistics: bool = Field(default=True, description="Include statistics")


class Setup(BaseModel):
    """Scenario setup configuration"""
    exchange: ExchangeSetup
    bot: Optional[BotSetup] = None
    recording: Optional[RecordingSetup] = None
    report: Optional[ReportSetup] = None


# Chaos Engineering Actions

class DelayEventChaos(BaseModel):
    """Delay a specific event"""
    type: Literal["delay_event"] = "delay_event"
    event: str = Field(description="Event name to delay")
    delay_ms: int = Field(description="Delay in milliseconds")
    at_cycle: Optional[int] = Field(default=None, description="Apply at specific cycle")
    after_event: Optional[str] = Field(default=None, description="Apply after specific event")


class InjectFailureChaos(BaseModel):
    """Inject a failure event"""
    type: Literal["inject_failure"] = "inject_failure"
    event: str = Field(description="Failed event to inject (e.g., MarketPriceFetchFailed)")
    at_cycle: Optional[int] = Field(default=None, description="Inject at specific cycle")
    after_event: Optional[str] = Field(default=None, description="Inject after specific event")
    error_message: str = Field(default="Chaos engineering injected failure")
    event_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional event properties (cycle_id, timestamp auto-populated if not provided)"
    )


class DropEventChaos(BaseModel):
    """Drop (don't publish) a specific event"""
    type: Literal["drop_event"] = "drop_event"
    event: str = Field(description="Event name to drop")
    at_cycle: Optional[int] = Field(default=None, description="Drop at specific cycle")
    probability: float = Field(default=1.0, ge=0.0, le=1.0, description="Probability of dropping (0.0-1.0)")


class ModifyEventChaos(BaseModel):
    """Modify event data"""
    type: Literal["modify_event"] = "modify_event"
    event: str = Field(description="Event name to modify")
    field: str = Field(description="Field to modify")
    value: Any = Field(description="New value")
    at_cycle: Optional[int] = Field(default=None, description="Modify at specific cycle")


class NetworkLatencyChaos(BaseModel):
    """Simulate network latency"""
    type: Literal["network_latency"] = "network_latency"
    min_delay_ms: int = Field(default=100, description="Min latency in ms")
    max_delay_ms: int = Field(default=1000, description="Max latency in ms")
    at_cycle: Optional[int] = Field(default=None, description="Apply at specific cycle")
    duration_cycles: int = Field(default=5, description="Duration in cycles")


ChaosAction = Union[
    DelayEventChaos,
    InjectFailureChaos,
    DropEventChaos,
    ModifyEventChaos,
    NetworkLatencyChaos
]


# Scenario Steps

class WaitForCyclesStep(BaseModel):
    """Wait for N monitoring cycles to complete"""
    wait_for_cycles: int = Field(description="Number of cycles to wait")


class WaitForEventStep(BaseModel):
    """Wait for a specific event"""
    wait_for_event: str = Field(description="Event name to wait for")
    timeout_seconds: int = Field(default=300, description="Timeout in seconds")


class WaitForTimeStep(BaseModel):
    """Wait for a specific duration"""
    wait_for_time: int = Field(description="Time to wait in seconds")


class EventCountAssertion(BaseModel):
    """Assert event count"""
    min: Optional[int] = Field(default=None, description="Minimum count")
    max: Optional[int] = Field(default=None, description="Maximum count")
    exact: Optional[int] = Field(default=None, description="Exact count")


class RangeAssertion(BaseModel):
    """Assert value is in range"""
    min: Optional[float] = Field(default=None, description="Minimum value")
    max: Optional[float] = Field(default=None, description="Maximum value")
    exact: Optional[float] = Field(default=None, description="Exact value")


class AssertionStep(BaseModel):
    """Assert conditions"""
    assert_: Dict[str, Any] = Field(alias="assert", description="Assertions to check")

    model_config = ConfigDict(populate_by_name=True)


ScenarioStep = Union[
    WaitForCyclesStep,
    WaitForEventStep,
    WaitForTimeStep,
    AssertionStep
]


# Main Scenario Schema

class TestScenario(BaseModel):
    """Complete test scenario definition"""
    name: str = Field(description="Scenario name")
    description: str = Field(description="Scenario description")
    setup: Setup = Field(description="Setup configuration")
    chaos: Optional[List[ChaosAction]] = Field(default=None, description="Chaos engineering actions")
    steps: List[Dict[str, Any]] = Field(description="Test steps")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Flash Crash Recovery",
                "description": "Verify bot handles flash crash",
                "setup": {
                    "exchange": {
                        "scenario": "flash_crash",
                        "initial_price": 50000.0
                    },
                    "bot": {
                        "initial_capital": 10000.0
                    }
                },
                "chaos": [
                    {
                        "type": "delay_event",
                        "event": "IndicatorsCalculated",
                        "delay_ms": 5000,
                        "at_cycle": 25
                    }
                ],
                "steps": [
                    {"wait_for_cycles": 50},
                    {
                        "assert": {
                            "event_count": {
                                "PositionPurchased": {"min": 3}
                            }
                        }
                    }
                ]
            }
        }
    )
