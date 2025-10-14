# Scenario Engine

**Generic scenario-based testing framework with chaos engineering and assertions for event-driven systems.**

## Overview

The Scenario Engine is a completely domain-agnostic framework for testing event-driven architectures. It provides:

- **Data Generation**: Abstract interfaces for generating domain-specific data
- **Scenario Profiles**: Configurable behavior patterns for data evolution
- **Chaos Engineering**: Inject failures, delays, and modifications into event streams
- **Assertion Framework**: Validate event streams with generic and custom assertions
- **Orchestration**: Declarative scenario steps with lifecycle management

## Architecture

### Generic Layer (in DevTools)

The generic components are completely domain-agnostic and can be used for any event-driven system:

```
scenario_engine/
├── interfaces.py          # Abstract base classes
│   ├── DataGenerator      # ABC for data generation
│   ├── ScenarioProfile    # ABC for behavior patterns
│   ├── MultiPhaseScenarioProfile
│   └── GeneratedData      # Generic container
├── chaos_injector.py      # Chaos engineering
│   ├── ChaosInjector
│   ├── DelayEvent
│   ├── DropEvent
│   ├── ModifyEvent
│   └── InjectFailureEvent
├── assertion_checker.py   # Assertion validation
│   ├── AssertionChecker
│   ├── EventCountAssertion
│   ├── EventSequenceAssertion
│   ├── NoEventAssertion
│   └── CustomAssertion
└── scenario_engine.py     # Orchestration engine
    ├── ScenarioEngine
    ├── ScenarioStep
    └── StepType
```

### Domain-Specific Layer (example: in Risk)

Domain-specific implementations extend the generic interfaces:

```
scenario_testing/
├── trading_data_generator.py    # Extends DataGenerator
│   └── TradingDataGenerator
├── market_scenarios.py           # Extends ScenarioProfile
│   ├── BullRunProfile
│   ├── BearCrashProfile
│   ├── FlashCrashProfile
│   ├── PumpAndDumpProfile
│   └── ... more profiles
└── example_usage.py             # Usage examples
```

## Quick Start

### 1. Create a Domain-Specific Data Generator

Extend `DataGenerator` to generate your domain-specific data:

```python
from python_pubsub_devtools.scenario_engine import DataGenerator, GeneratedData


class MyDataGenerator(DataGenerator):

    def generate_next(self) -> GeneratedData:
        # Your domain-specific logic
        value = self.scenario_profile.calculate_next_value(
            self.current_value,
            self.call_count,
            self.history
        )

        data = GeneratedData(
            primary_value=value,
            secondary_values={"extra": "data"},
            metadata={"source": "my_generator"}
        )

        self.history.append(data)
        self.call_count += 1

        return data

    def reset(self):
        self.call_count = 0
        self.history.clear()
```

### 2. Create Scenario Profiles

Extend `ScenarioProfile` to define behavior patterns:

```python
from python_pubsub_devtools.scenario_engine import ScenarioProfile


class SteadyGrowthProfile(ScenarioProfile):

    def __init__(self, growth_rate: float = 0.01):
        super().__init__(
            name="Steady Growth",
            description="Steady growth pattern",
            growth_rate=growth_rate
        )

    def calculate_next_value(self, current_value, call_count, history):
        growth_rate = self.parameters["growth_rate"]
        return current_value * (1 + growth_rate)
```

### 3. Run a Scenario

```python
from python_pubsub_devtools.scenario_engine import (
    ScenarioEngine,
    ScenarioStep,
    StepType,
    EventCountAssertion
)

# Create generator with profile
profile = SteadyGrowthProfile(growth_rate=0.02)
generator = MyDataGenerator(scenario_profile=profile)

# Create engine
engine = ScenarioEngine(
    generator=generator,
    service_bus=my_service_bus,
    enable_chaos=False
)

# Define scenario
scenario = [
    ScenarioStep(
        step_type=StepType.WAIT_CYCLES,
        name="Generate 50 data points",
        cycles=50
    ),
    ScenarioStep(
        step_type=StepType.RUN_ASSERTIONS,
        name="Verify results",
        assertions=[
            EventCountAssertion("DataGenerated", min_count=50)
        ]
    )
]

# Run
report = engine.run_scenario(
    steps=scenario,
    context={"name": "Growth Test"}
)

# Print report
engine.print_report(report)
```

## Features

### Chaos Engineering

Inject various types of chaos into your event stream:

```python
from python_pubsub_devtools.scenario_engine import (
    DelayEvent,
    DropEvent,
    ModifyEvent,
    InjectFailureEvent
)

# Create engine with chaos
engine = ScenarioEngine(
    generator=generator,
    service_bus=service_bus,
    enable_chaos=True
)

# Add chaos actions
engine.chaos_injector.add_action(
    DelayEvent(
        event_pattern="DataProcessed",
        delay_ms=5000,
        at_cycle=10
    )
)

engine.chaos_injector.add_action(
    DropEvent(
        event_pattern="DataProcessed",
        probability=0.1  # 10% chance
    )
)

engine.chaos_injector.add_action(
    ModifyEvent(
        event_pattern="PriceUpdate",
        field_path="price.value",
        new_value=0.0,
        at_cycle=20
    )
)

engine.chaos_injector.add_action(
    InjectFailureEvent(
        trigger_pattern="DataFetched",
        failure_event_name="DataFetchFailed",
        failure_data={"error": "Simulated failure"}
    )
)
```

### Assertions

Validate your event streams:

```python
from python_pubsub_devtools.scenario_engine import (
    EventCountAssertion,
    EventSequenceAssertion,
    NoEventAssertion,
    CustomAssertion
)

assertions = [
    # Count assertions
    EventCountAssertion("DataFetched", exact_count=100),
    EventCountAssertion("DataProcessed", min_count=90),

    # Sequence assertions
    EventSequenceAssertion(
        expected_sequence=["Started", "Processing", "Completed"],
        allow_gaps=True
    ),

    # Negative assertions
    NoEventAssertion("ErrorOccurred"),

    # Custom assertions
    CustomAssertion("my_check", my_custom_check_function)
]
```

### Multi-Phase Scenarios

Create complex scenarios with multiple phases:

```python
from python_pubsub_devtools.scenario_engine import MultiPhaseScenarioProfile, ScenarioPhase


class MyMultiPhaseProfile(MultiPhaseScenarioProfile):

    def __init__(self):
        phases = [
            {
                "name": ScenarioPhase.NORMAL.value,
                "duration": 10,
                "behavior": "stable"
            },
            {
                "name": ScenarioPhase.CRITICAL.value,
                "duration": 5,
                "behavior": "crisis"
            },
            {
                "name": ScenarioPhase.RECOVERY.value,
                "duration": 20,
                "behavior": "recovery"
            }
        ]

        super().__init__(name="Crisis Recovery", phases=phases)

    def calculate_phase_value(self, phase, current_value, phase_progress):
        behavior = phase.get("behavior")

        if behavior == "stable":
            return current_value
        elif behavior == "crisis":
            return current_value * 0.95  # Decline
        elif behavior == "recovery":
            return current_value * 1.02  # Recovery

        return current_value
```

## Scenario Steps

Available step types:

- **WAIT_CYCLES**: Wait for N cycles of data generation
- **WAIT_EVENT**: Wait for a specific event to occur
- **RUN_ASSERTIONS**: Run assertions on recorded events
- **EXECUTE_ACTION**: Execute a custom action
- **GENERATE_DATA**: Generate data without advancing cycles

## Example: Trading Scenarios

See `Python.PubSub.Risk/python_pubsub_risk/scenario_testing/` for a complete example of domain-specific implementations:

- `TradingDataGenerator`: Generates market price data
- `BullRunProfile`, `BearCrashProfile`, `FlashCrashProfile`, etc.: Trading scenario profiles
- `example_usage.py`: Complete usage examples

## Design Principles

1. **Separation of Concerns**: Generic infrastructure separate from domain logic
2. **Dependency Injection**: All domain-specific behavior injected via interfaces
3. **Composability**: Mix and match profiles, chaos actions, and assertions
4. **Declarative**: Define scenarios as data structures, not code
5. **Testability**: Everything is testable in isolation

## Extending the Framework

### For New Domains

1. Create a `DataGenerator` subclass for your domain
2. Create `ScenarioProfile` subclasses for your behavior patterns
3. Optionally create domain-specific assertions
4. Use the generic `ScenarioEngine` as-is

### For New Chaos Actions

1. Extend `ChaosAction` base class
2. Implement `should_apply()` and `apply()` methods
3. Add to the chaos injector

### For New Assertion Types

1. Extend `Assertion` base class
2. Implement `check()` method
3. Return `AssertionResult`

## Best Practices

1. **Keep profiles simple**: One profile = one behavior pattern
2. **Use multi-phase for complex scenarios**: Don't create monolithic profiles
3. **Test with chaos early**: Find resilience issues before production
4. **Create custom assertions**: Domain-specific validations are powerful
5. **Document your profiles**: Clear names and descriptions help users

## API Reference

See the docstrings in each module for detailed API documentation:

- `interfaces.py`: Core abstractions
- `chaos_injector.py`: Chaos engineering API
- `assertion_checker.py`: Assertion framework API
- `scenario_engine.py`: Orchestration API

## License

MIT License - see LICENSE file for details
