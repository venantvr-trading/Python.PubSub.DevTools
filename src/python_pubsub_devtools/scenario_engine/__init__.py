"""
Scenario Engine Module

Provides generic tools for scenario-based testing with chaos engineering.
"""

from .interfaces import DataGenerator, ScenarioProfile, GeneratedData, MultiPhaseScenarioProfile, ScenarioPhase
from .chaos_injector import (
    ChaosInjector,
    ChaosAction,
    DelayEvent,
    DropEvent,
    ModifyEvent,
    InjectFailureEvent
)
from .assertion_checker import (
    AssertionChecker,
    AssertionResult,
    Assertion,
    EventCountAssertion,
    EventSequenceAssertion,
    NoEventAssertion,
    CustomAssertion
)
from .scenario_engine import ScenarioEngine, ScenarioStep, StepType

__all__ = [
    # Interfaces
    "DataGenerator",
    "ScenarioProfile",
    "GeneratedData",
    "MultiPhaseScenarioProfile",
    "ScenarioPhase",
    # Chaos
    "ChaosInjector",
    "ChaosAction",
    "DelayEvent",
    "DropEvent",
    "ModifyEvent",
    "InjectFailureEvent",
    # Assertions
    "AssertionChecker",
    "AssertionResult",
    "Assertion",
    "EventCountAssertion",
    "EventSequenceAssertion",
    "NoEventAssertion",
    "CustomAssertion",
    # Engine
    "ScenarioEngine",
    "ScenarioStep",
    "StepType",
]
