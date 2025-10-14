"""
Generic Scenario Engine

Orchestrates scenario-based testing with data generation, chaos injection, and assertions.
Completely domain-agnostic.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .assertion_checker import AssertionChecker
from .chaos_injector import ChaosInjector
from .interfaces import DataGenerator


class StepType(Enum):
    """Types of scenario steps"""
    WAIT_CYCLES = "wait_cycles"
    WAIT_EVENT = "wait_event"
    RUN_ASSERTIONS = "run_assertions"
    EXECUTE_ACTION = "execute_action"
    GENERATE_DATA = "generate_data"


@dataclass
class ScenarioStep:
    """A step in a scenario

    Examples:
        # Wait for 10 cycles
        ScenarioStep(StepType.WAIT_CYCLES, cycles=10)

        # Wait for a specific event
        ScenarioStep(StepType.WAIT_EVENT, event_name="DataProcessed")

        # Run assertions
        ScenarioStep(StepType.RUN_ASSERTIONS, assertions=[...])

        # Execute custom action
        ScenarioStep(StepType.EXECUTE_ACTION, action=lambda: print("Custom"))

        # Generate data
        ScenarioStep(StepType.GENERATE_DATA, count=5)
    """
    step_type: StepType
    name: str = ""
    cycles: Optional[int] = None
    event_name: Optional[str] = None
    assertions: Optional[List] = None
    action: Optional[Callable] = None
    count: Optional[int] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ScenarioEngine:
    """Generic scenario engine for event-driven systems

    Usage:
        # Create data generator (domain-specific)
        generator = MyDataGenerator(scenario_profile, **config)

        # Create engine
        engine = ScenarioEngine(
            generator=generator,
            service_bus=service_bus
        )

        # Add chaos (optional)
        engine.chaos_injector.add_action(DelayEvent("DataFetched", delay_ms=5000))

        # Define scenario
        scenario = [
            ScenarioStep(StepType.WAIT_CYCLES, name="Warmup", cycles=5),
            ScenarioStep(StepType.WAIT_EVENT, name="Wait for processing", event_name="Processed"),
            ScenarioStep(StepType.RUN_ASSERTIONS, name="Verify results", assertions=[...])
        ]

        # Run scenario
        report = engine.run_scenario(scenario)
    """

    def __init__(
            self,
            generator: DataGenerator,
            service_bus: Any,
            enable_chaos: bool = False,
            record_events: bool = True
    ):
        """Initialize scenario engine

        Args:
            generator: DataGenerator instance (domain-specific)
            service_bus: Service bus with publish() method
            enable_chaos: Whether to enable chaos injection
            record_events: Whether to record events for assertions
        """
        self.generator = generator
        self.service_bus = service_bus
        self.record_events = record_events

        # Event recording
        self.recorded_events: List[Dict[str, Any]] = []
        self.event_counts: Dict[str, int] = {}

        # Chaos injection
        self.chaos_injector: Optional[ChaosInjector] = None
        if enable_chaos:
            self.chaos_injector = ChaosInjector()

        # Assertion checking
        self.assertion_checker: Optional[AssertionChecker] = None

        # Scenario state
        self.current_cycle = 0
        self.scenario_start_time: Optional[datetime] = None
        self.scenario_end_time: Optional[datetime] = None
        self.current_step_index = 0

        # Subscribe to events for recording
        if self.record_events:
            self._setup_event_recording()

    def _setup_event_recording(self):
        """Setup event recording by wrapping the service bus publish method"""
        original_publish = self.service_bus.publish

        def recording_publish(event_name: str, event_data: Any, source: str):
            """Wrapped publish that records events"""
            # Record event
            self.recorded_events.append({
                "event_name": event_name,
                "event_data": event_data,
                "source": source,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cycle": self.current_cycle
            })

            # Update counts
            self.event_counts[event_name] = self.event_counts.get(event_name, 0) + 1

            # Call original publish
            original_publish(event_name, event_data, source)

        self.service_bus.publish = recording_publish

    def run_scenario(
            self,
            steps: List[ScenarioStep],
            context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run a scenario with multiple steps

        Args:
            steps: List of scenario steps to execute
            context: Optional context dict with scenario configuration

        Returns:
            Dict with scenario execution report
        """
        self.scenario_start_time = datetime.now(timezone.utc)
        context = context or {}

        print(f"\n{'=' * 80}")
        print(f"STARTING SCENARIO: {context.get('name', 'Unnamed')}")
        print(f"{'=' * 80}\n")

        # Reset state
        self.current_cycle = 0
        self.current_step_index = 0
        self.recorded_events.clear()
        self.event_counts.clear()
        self.generator.reset()

        # Enable chaos if configured
        if self.chaos_injector:
            self.chaos_injector.wrap_service_bus(self.service_bus)

        # Execute steps
        step_results = []
        for i, step in enumerate(steps):
            self.current_step_index = i
            print(f"\n--- Step {i + 1}/{len(steps)}: {step.name or step.step_type.value} ---")

            result = self._execute_step(step, context)
            step_results.append(result)

            if not result.get("success", False):
                print(f"❌ Step failed: {result.get('error', 'Unknown error')}")
                break

        # Disable chaos
        if self.chaos_injector:
            self.chaos_injector.unwrap_service_bus()

        self.scenario_end_time = datetime.now(timezone.utc)

        # Generate report
        report = self._generate_report(steps, step_results, context)

        print(f"\n{'=' * 80}")
        print(f"SCENARIO COMPLETED")
        print(f"{'=' * 80}\n")

        return report

    def _execute_step(
            self,
            step: ScenarioStep,
            context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single scenario step

        Args:
            step: ScenarioStep to execute
            context: Scenario context

        Returns:
            Dict with step execution result
        """
        start_time = datetime.now(timezone.utc)

        try:
            if step.step_type == StepType.WAIT_CYCLES:
                result = self._wait_cycles(step.cycles or 1)

            elif step.step_type == StepType.WAIT_EVENT:
                result = self._wait_event(step.event_name, timeout_cycles=step.cycles)

            elif step.step_type == StepType.RUN_ASSERTIONS:
                result = self._run_assertions(step.assertions or [], context)

            elif step.step_type == StepType.EXECUTE_ACTION:
                result = self._execute_action(step.action)

            elif step.step_type == StepType.GENERATE_DATA:
                result = self._generate_data(step.count or 1)

            else:
                result = {
                    "success": False,
                    "error": f"Unknown step type: {step.step_type}"
                }

            end_time = datetime.now(timezone.utc)
            result["duration"] = (end_time - start_time).total_seconds()
            result["step_type"] = step.step_type.value
            result["step_name"] = step.name

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "step_type": step.step_type.value,
                "step_name": step.name
            }

    def _wait_cycles(self, cycles: int) -> Dict[str, Any]:
        """Wait for a number of cycles"""
        print(f"⏳ Waiting for {cycles} cycle(s)...")

        for i in range(cycles):
            # Generate data for this cycle
            data = self.generator.generate_next()
            print(f"  Cycle {self.current_cycle + 1}: Generated {data.primary_value}")

            # Publish event (if generator has a publish method or we inject one)
            # This is where domain-specific logic would come in
            # For now, just increment cycle
            self.current_cycle += 1

        return {
            "success": True,
            "cycles_completed": cycles,
            "final_cycle": self.current_cycle
        }

    def _wait_event(
            self,
            event_name: str,
            timeout_cycles: Optional[int] = None
    ) -> Dict[str, Any]:
        """Wait for a specific event to occur"""
        print(f"⏳ Waiting for event: {event_name}")

        start_cycle = self.current_cycle
        timeout = timeout_cycles or 100  # Default timeout

        while (self.current_cycle - start_cycle) < timeout:
            # Check if event occurred
            if event_name in self.event_counts:
                print(f"✅ Event {event_name} occurred!")
                return {
                    "success": True,
                    "event_name": event_name,
                    "occurred_at_cycle": self.current_cycle
                }

            # Continue cycling
            data = self.generator.generate_next()
            self.current_cycle += 1

        return {
            "success": False,
            "error": f"Event {event_name} did not occur within {timeout} cycles"
        }

    def _run_assertions(
            self,
            assertions: List,
            context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run assertions on recorded events"""
        print(f"🔍 Running {len(assertions)} assertion(s)...")

        # Create assertion checker
        checker = AssertionChecker(self.recorded_events, context)
        checker.add_assertions(assertions)

        # Check all assertions
        results = checker.check_all()

        # Print results
        for result in results:
            status = "✅" if result.passed else "❌"
            print(f"  {status} {result.name}: {result.message}")

        return {
            "success": checker.all_passed(),
            "total_assertions": len(results),
            "passed": len([r for r in results if r.passed]),
            "failed": len([r for r in results if not r.passed]),
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "expected": r.expected,
                    "actual": r.actual
                }
                for r in results
            ]
        }

    def _execute_action(self, action: Optional[Callable]) -> Dict[str, Any]:
        """Execute custom action"""
        if not action:
            return {"success": False, "error": "No action provided"}

        print(f"⚡ Executing custom action...")

        try:
            result = action()
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_data(self, count: int) -> Dict[str, Any]:
        """Generate data without advancing cycles"""
        print(f"🎲 Generating {count} data point(s)...")

        generated = []
        for i in range(count):
            data = self.generator.generate_next()
            generated.append(data)
            print(f"  Generated: {data.primary_value}")

        return {
            "success": True,
            "count": count,
            "data": generated
        }

    def _generate_report(
            self,
            steps: List[ScenarioStep],
            step_results: List[Dict[str, Any]],
            context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive scenario report"""
        duration = (self.scenario_end_time - self.scenario_start_time).total_seconds()

        # Count successes/failures
        successful_steps = len([r for r in step_results if r.get("success", False)])
        failed_steps = len([r for r in step_results if not r.get("success", True)])

        # Generator statistics
        generator_stats = self.generator.get_statistics()

        # Chaos statistics
        chaos_stats = None
        if self.chaos_injector:
            chaos_stats = self.chaos_injector.get_statistics()

        report = {
            "scenario_name": context.get("name", "Unnamed"),
            "start_time": self.scenario_start_time.isoformat(),
            "end_time": self.scenario_end_time.isoformat(),
            "duration_seconds": duration,
            "total_cycles": self.current_cycle,
            "total_steps": len(steps),
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "step_results": step_results,
            "event_statistics": {
                "total_events": len(self.recorded_events),
                "unique_events": len(self.event_counts),
                "event_counts": self.event_counts
            },
            "generator_statistics": generator_stats,
            "chaos_statistics": chaos_stats,
            "context": context
        }

        return report

    def print_report(self, report: Dict[str, Any]):
        """Print human-readable scenario report"""
        print("\n" + "=" * 80)
        print("SCENARIO REPORT")
        print("=" * 80)

        print(f"\nScenario: {report['scenario_name']}")
        print(f"Duration: {report['duration_seconds']:.2f}s")
        print(f"Total Cycles: {report['total_cycles']}")

        print(f"\nSteps: {report['successful_steps']}/{report['total_steps']} passed")
        if report['failed_steps'] > 0:
            print(f"❌ {report['failed_steps']} step(s) failed")

        print(f"\nEvents:")
        print(f"  Total: {report['event_statistics']['total_events']}")
        print(f"  Unique: {report['event_statistics']['unique_events']}")

        if report['chaos_statistics']:
            print(f"\nChaos Injection:")
            print(f"  Actions: {report['chaos_statistics']['chaos_actions']}")
            print(f"  Events affected: {report['chaos_statistics']['total_events']}")

        print("\n" + "=" * 80)
