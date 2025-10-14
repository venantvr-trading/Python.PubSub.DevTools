"""
Generic Interfaces for Scenario Engine

Provides abstract base classes that domain-specific implementations must extend.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


@dataclass
class GeneratedData:
    """Container for generated data from a DataGenerator

    This is a generic container that can hold any type of data.
    Domain-specific generators should populate this with relevant data.
    """
    primary_value: Any  # Main data point (e.g., price, temperature, count)
    secondary_values: Dict[str, Any] = None  # Additional data (e.g., bid/ask, min/max)
    metadata: Dict[str, Any] = None  # Metadata (e.g., timestamp, source)
    time_series: Any = None  # Historical data (e.g., DataFrame, list)

    def __post_init__(self):
        if self.secondary_values is None:
            self.secondary_values = {}
        if self.metadata is None:
            self.metadata = {}


class DataGenerator(ABC):
    """Abstract base class for data generators

    A DataGenerator produces data according to a scenario profile.
    Domain-specific implementations define what kind of data to generate.

    Examples:
        - TradingDataGenerator: generates market prices
        - SensorDataGenerator: generates sensor readings
        - TrafficDataGenerator: generates network traffic metrics
    """

    def __init__(self, scenario_profile: 'ScenarioProfile', **config):
        """Initialize data generator

        Args:
            scenario_profile: Profile defining data generation behavior
            **config: Additional configuration parameters
        """
        self.scenario_profile = scenario_profile
        self.config = config
        self.call_count = 0
        self.history: List[GeneratedData] = []

    @abstractmethod
    def generate_next(self) -> GeneratedData:
        """Generate next data point based on scenario

        Returns:
            GeneratedData: Container with generated data
        """
        pass

    @abstractmethod
    def reset(self):
        """Reset generator to initial state"""
        pass

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about generated data

        Returns:
            Dict with statistics (implementation-specific)
        """
        return {
            "call_count": self.call_count,
            "history_length": len(self.history)
        }


class ScenarioProfile(ABC):
    """Abstract base class for scenario profiles

    A ScenarioProfile defines the behavior pattern for data generation.
    It encapsulates the logic of how data should evolve over time.

    Examples:
        - MarketScenarioProfile: bull/bear markets, crashes, volatility
        - FailureScenarioProfile: gradual degradation, sudden failures
        - LoadScenarioProfile: ramp-up, sustained load, spike patterns
    """

    def __init__(self, name: str, description: str = "", **parameters):
        """Initialize scenario profile

        Args:
            name: Unique scenario name
            description: Human-readable description
            **parameters: Profile-specific parameters
        """
        self.name = name
        self.description = description
        self.parameters = parameters

    @abstractmethod
    def calculate_next_value(self, current_value: Any, call_count: int, history: List[Any]) -> Any:
        """Calculate next value based on scenario logic

        Args:
            current_value: Current value
            call_count: Number of times data has been generated
            history: Historical values

        Returns:
            Next value according to scenario pattern
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """Get scenario profile information

        Returns:
            Dict with name, description, and parameters
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class ScenarioPhase(Enum):
    """Common phases in multi-phase scenarios"""
    INITIALIZATION = "initialization"
    NORMAL = "normal"
    TRANSITION = "transition"
    CRITICAL = "critical"
    RECOVERY = "recovery"
    STABILIZATION = "stabilization"


class MultiPhaseScenarioProfile(ScenarioProfile):
    """Base class for scenarios with multiple phases

    Useful for scenarios that have distinct phases:
    - Flash crash: normal → crash → recovery
    - Load test: ramp-up → sustained → ramp-down
    - Failure simulation: normal → degradation → failure → recovery
    """

    def __init__(self, name: str, phases: List[Dict[str, Any]], **parameters):
        """Initialize multi-phase scenario

        Args:
            name: Scenario name
            phases: List of phase definitions with duration and behavior
            **parameters: Additional parameters
        """
        super().__init__(name, **parameters)
        self.phases = phases
        self.current_phase_index = 0

    def get_current_phase(self, call_count: int) -> Dict[str, Any]:
        """Determine current phase based on call count

        Args:
            call_count: Current call count

        Returns:
            Current phase definition
        """
        accumulated_duration = 0
        for phase in self.phases:
            duration = phase.get("duration", 0)
            if call_count < accumulated_duration + duration:
                return phase
            accumulated_duration += duration

        # Return last phase if we're past all durations
        return self.phases[-1] if self.phases else {}

    @abstractmethod
    def calculate_phase_value(self, phase: Dict[str, Any], current_value: Any,
                              phase_progress: float) -> Any:
        """Calculate value within a specific phase

        Args:
            phase: Current phase definition
            current_value: Current value
            phase_progress: Progress within phase (0.0 to 1.0)

        Returns:
            Next value for this phase
        """
        pass

    def calculate_next_value(self, current_value: Any, call_count: int,
                             history: List[Any]) -> Any:
        """Calculate next value based on current phase"""
        phase = self.get_current_phase(call_count)

        # Calculate progress within current phase
        accumulated_duration = sum(p.get("duration", 0) for p in self.phases[:self.current_phase_index])
        phase_duration = phase.get("duration", 1)
        calls_in_phase = call_count - accumulated_duration
        phase_progress = min(1.0, calls_in_phase / phase_duration) if phase_duration > 0 else 1.0

        return self.calculate_phase_value(phase, current_value, phase_progress)
