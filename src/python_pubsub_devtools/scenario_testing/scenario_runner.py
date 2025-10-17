"""
Scenario Runner - Orchestrates declarative scenario testing with chaos engineering.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .assertion_checker import AssertionChecker, AssertionResult
from .chaos_injector import ChaosInjector
from .scenario_schema import TestScenario

logger = logging.getLogger(__name__)


@dataclass
class ScenarioResult:
    """
    Result of a scenario execution.

    Attributes:
        scenario: The test scenario that was executed
        passed: Whether all assertions passed
        duration_ms: Execution duration in milliseconds
        assertion_results: List of assertion check results
        error: Exception if scenario failed unexpectedly
        events_recorded: Number of events recorded during execution
    """
    scenario: TestScenario
    passed: bool
    duration_ms: float
    assertion_results: List[AssertionResult] = field(default_factory=list)
    error: Optional[Exception] = None
    events_recorded: int = 0

    @property
    def status(self) -> str:
        """Get human-readable status"""
        if self.error:
            return "ERROR"
        return "PASS" if self.passed else "FAIL"


class ScenarioRunner:
    """
    Orchestrates scenario execution with chaos engineering and assertions.

    Manages:
    - Loading scenarios from YAML files
    - Publishing initial events
    - Injecting chaos actions
    - Recording events for assertion checking
    - Running assertions
    - Generating test reports

    Zero-coupling design: Works with any ServiceBus without requiring
    application event classes.
    """

    def __init__(
            self,
            service_bus: Any,
            event_registry: Optional[Dict[str, type]] = None,
            on_event_callback: Optional[Callable[[str, Any], None]] = None
    ):
        """
        Initialize scenario runner.

        Args:
            service_bus: ServiceBus instance to use for publishing events
            event_registry: Optional dict mapping event names to event classes
            on_event_callback: Optional callback for event notifications
        """
        self.service_bus = service_bus
        self.event_registry = event_registry or {}
        self.on_event_callback = on_event_callback

        self.assertion_checker = AssertionChecker()
        self.chaos_injector = ChaosInjector(service_bus, event_registry)

        # Monkey-patch service_bus to record all published events
        self._original_publish: Optional[Callable] = None
        self._setup_event_recording()

    def _setup_event_recording(self) -> None:
        """
        Set up event recording by monkey-patching service_bus.publish.

        This allows the AssertionChecker to observe all events without
        requiring changes to the application code.
        """
        if self._original_publish:
            return  # Already set up

        self._original_publish = self.service_bus.publish

        def recording_publish(event_name: str, event: Any, source: str):
            """Wrapped publish that records events"""
            # Record for assertions
            self.assertion_checker.record_event(event_name, event)

            # Notify callback if provided
            if self.on_event_callback:
                try:
                    self.on_event_callback(event_name, event)
                except Exception as e:
                    logger.warning(f"Event callback failed: {e}")

            # Call original publish (or chaos-wrapped version)
            return self._original_publish(event_name, event, source)

        self.service_bus.publish = recording_publish

    def run_scenario(self, scenario: TestScenario) -> ScenarioResult:
        """
        Run a single test scenario.

        Args:
            scenario: TestScenario to execute

        Returns:
            ScenarioResult with execution outcome
        """
        logger.info(f"Starting scenario: {scenario.name}")
        start_time = time.time()

        try:
            # Clear previous state
            self.assertion_checker.clear()

            # Start chaos injection if any chaos actions defined
            if scenario.chaos:
                self.chaos_injector.start(scenario.chaos)
                logger.info(f"Chaos injection started with {len(scenario.chaos)} action(s)")

            # Publish initial events
            self._publish_initial_events(scenario)

            # Wait for scenario timeout
            timeout_sec = scenario.timeout_ms / 1000.0
            logger.info(f"Waiting {timeout_sec}s for scenario to complete...")
            time.sleep(timeout_sec)

            # Stop chaos injection
            if scenario.chaos:
                self.chaos_injector.stop()

            # Check assertions
            assertion_results = self.assertion_checker.check_all_assertions(scenario.assertions)

            # Determine if scenario passed
            passed = all(r.passed for r in assertion_results)

            duration_ms = (time.time() - start_time) * 1000
            events_recorded = len(self.assertion_checker.recorded_events)

            result = ScenarioResult(
                scenario=scenario,
                passed=passed,
                duration_ms=duration_ms,
                assertion_results=assertion_results,
                events_recorded=events_recorded
            )

            logger.info(
                f"Scenario completed: {scenario.name} "
                f"({result.status}, {duration_ms:.0f}ms, {events_recorded} events)"
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Scenario failed with error: {e}", exc_info=True)

            # Stop chaos injection if it was started
            try:
                self.chaos_injector.stop()
            except Exception:
                pass

            return ScenarioResult(
                scenario=scenario,
                passed=False,
                duration_ms=duration_ms,
                error=e,
                events_recorded=len(self.assertion_checker.recorded_events)
            )

    def _publish_initial_events(self, scenario: TestScenario) -> None:
        """
        Publish initial events defined in scenario.

        Args:
            scenario: TestScenario containing initial events
        """
        if not scenario.initial_events:
            return

        logger.info(f"Publishing {len(scenario.initial_events)} initial event(s)")

        for event_spec in scenario.initial_events:
            event_name = event_spec.get('event_name')
            event_data = event_spec.get('event_data', {})

            if not event_name:
                logger.warning("Skipping initial event with no event_name")
                continue

            # Create event instance
            event = self.chaos_injector.create_event_from_data(event_name, event_data)

            # Publish event
            try:
                self.service_bus.publish(event_name, event, source="scenario_runner")
                logger.debug(f"Published: {event_name}")
            except Exception as e:
                logger.error(f"Failed to publish {event_name}: {e}")

    def run_scenarios_from_directory(self, scenarios_dir: Path, tags: Optional[List[str]] = None) -> List[ScenarioResult]:
        """
        Run all scenarios from a directory.

        Args:
            scenarios_dir: Directory containing YAML scenario files
            tags: Optional list of tags to filter scenarios

        Returns:
            List of ScenarioResults
        """
        scenarios_path = Path(scenarios_dir)

        if not scenarios_path.exists():
            raise FileNotFoundError(f"Scenarios directory not found: {scenarios_dir}")

        # Load all scenario files
        scenario_files = list(scenarios_path.glob("*.yaml")) + list(scenarios_path.glob("*.yml"))

        if not scenario_files:
            logger.warning(f"No scenario files found in {scenarios_dir}")
            return []

        logger.info(f"Found {len(scenario_files)} scenario file(s)")

        # Load and filter scenarios
        scenarios: List[TestScenario] = []
        for file_path in scenario_files:
            try:
                scenario = TestScenario.from_yaml_file(str(file_path))

                # Filter by tags if specified
                if tags:
                    if not any(tag in scenario.tags for tag in tags):
                        logger.debug(f"Skipping {scenario.name} (tags don't match)")
                        continue

                scenarios.append(scenario)
            except Exception as e:
                logger.error(f"Failed to load scenario from {file_path}: {e}")

        if not scenarios:
            logger.warning("No scenarios to run after filtering")
            return []

        logger.info(f"Running {len(scenarios)} scenario(s)")

        # Run all scenarios
        results = []
        for scenario in scenarios:
            result = self.run_scenario(scenario)
            results.append(result)

        # Print summary
        self._print_summary(results)

        return results

    def _print_summary(self, results: List[ScenarioResult]) -> None:
        """
        Print execution summary.

        Args:
            results: List of ScenarioResults
        """
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        logger.info("\n" + "=" * 60)
        logger.info(f"SCENARIO SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total:  {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info("=" * 60)

        for result in results:
            status_icon = "PASS" if result.passed else "FAIL"
            logger.info(
                f"{status_icon} {result.scenario.name}: {result.status} "
                f"({result.duration_ms:.0f}ms, {result.events_recorded} events)"
            )

            if not result.passed:
                # Print failed assertions
                for assertion_result in result.assertion_results:
                    if not assertion_result.passed:
                        logger.info(f"   FAIL: {assertion_result.message}")

        logger.info("=" * 60 + "\n")

    def cleanup(self) -> None:
        """
        Clean up and restore original service_bus.publish.
        """
        if self._original_publish:
            self.service_bus.publish = self._original_publish
            self._original_publish = None

        self.chaos_injector.stop()
        self.assertion_checker.clear()

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.cleanup()
