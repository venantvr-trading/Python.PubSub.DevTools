#!/usr/bin/env python3
"""
Scenario Runner

Executes declarative test scenarios with chaos engineering and assertions.
"""
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Add tools directories to path for cross-module imports
sys.path.insert(0, str(Path(__file__).parent.parent / "mock_exchange"))
sys.path.insert(0, str(Path(__file__).parent.parent / "event_recorder"))

# Runtime imports - using relative imports for same-package modules
from .scenario_schema import TestScenario
from .chaos_injector import ChaosInjector
from .assertion_checker import AssertionChecker, AssertionResult

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScenarioRunner:
    """Runs declarative test scenarios"""

    def __init__(self, service_bus: Any, event_registry=None):
        """Initialize scenario runner

        Args:
            service_bus: The service bus instance to use for chaos and assertions.
            event_registry: Optional event registry for chaos injector. Can be:
                - Dict[str, type]: Mapping of event names to classes
                - Callable: Factory function (event_name, event_data) -> event
                - None: Use SimpleNamespace (zero coupling, default)
        """
        self.service_bus = service_bus
        self.event_registry = event_registry
        self.scenario: Optional[TestScenario] = None  # type: ignore
        self.chaos_injector: Optional[ChaosInjector] = None

        # Results
        self.start_time = None
        self.end_time = None
        self.assertion_results: List[AssertionResult] = []
        self.events = []

    def load_scenario(self, scenario_path: str | Path) -> TestScenario:
        """Load scenario from YAML file"""
        logger.info(f"📖 Loading scenario from {scenario_path}")

        with open(scenario_path, 'r') as f:
            data = yaml.safe_load(f)

        self.scenario = TestScenario(**data)
        logger.info(f"✅ Loaded scenario: {self.scenario.name}")  # type: ignore
        logger.info(f"   {self.scenario.description}")  # type: ignore

        return self.scenario

    def setup_chaos(self, service_bus) -> Optional[ChaosInjector]:
        """Setup chaos engineering"""
        if not self.scenario.chaos:
            return None

        logger.info(f"🔥 Setting up chaos engineering with {len(self.scenario.chaos)} actions")

        self.chaos_injector = ChaosInjector(
            service_bus,
            self.scenario.chaos,
            event_registry=self.event_registry
        )
        self.chaos_injector.start()

        return self.chaos_injector

    def run_steps(self):
        """Execute scenario steps"""
        logger.info(f"🏃 Running {len(self.scenario.steps)} steps...")

        for i, step in enumerate(self.scenario.steps, 1):
            logger.info(f"📍 Step {i}/{len(self.scenario.steps)}: {step}")

            if "wait_for_cycles" in step:
                self._wait_for_cycles(step["wait_for_cycles"])

            elif "wait_for_event" in step:
                self._wait_for_event(step["wait_for_event"], step.get("timeout_seconds", 300))

            elif "wait_for_time" in step:
                self._wait_for_time(step["wait_for_time"])

            elif "assert" in step:
                self._check_assertions(step["assert"])

            else:
                logger.warning(f"Unknown step type: {step}")

    def _wait_for_cycles(self, cycle_count: int):
        """Wait for N monitoring cycles to complete"""
        logger.info(f"⏳ Waiting for {cycle_count} cycles...")

        # This is now a simple time-based wait, as cycles are driven by mock_exchange replay.
        time.sleep(cycle_count * 0.1)  # Approximate wait

        logger.info(f"✅ Completed {cycle_count} cycles")

    def _wait_for_event(self, event_name: str, timeout_seconds: int):
        """Wait for specific event to occur"""
        logger.info(f"⏳ Waiting for event {event_name} (timeout: {timeout_seconds}s)...")

        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            # Check if event has occurred
            if self.recorder and any(e['event_name'] == event_name for e in self.recorder.events):
                logger.info(f"✅ Event {event_name} received")
                return
            time.sleep(0.5)

        logger.warning(f"⚠️  Timeout waiting for event {event_name}")

    def _wait_for_time(self, seconds: int):
        """Wait for specific duration"""
        logger.info(f"⏳ Waiting for {seconds} seconds...")
        time.sleep(seconds)
        logger.info(f"✅ Wait complete")

    def _check_assertions(self, assertions: Dict[str, Any]):
        """Check assertions"""
        logger.info(f"🔍 Checking assertions...")

        # TODO: Collect events from the Event Recorder API instead of a direct object reference.
        # For now, this part needs to be adapted to fetch events.
        events = []  # Placeholder

        # Create assertion checker
        checker = AssertionChecker(events)
        results = checker.check_assertions(assertions)

        self.assertion_results.extend(results)

        # Log results
        for result in results:
            logger.info(f"   {result}")

    def teardown(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up...")

        if self.chaos_injector:
            self.chaos_injector.stop()

    def run(self, scenario_path: str | Path) -> Dict[str, Any]:
        """Execute complete scenario

        Returns:
            Dict with test results
        """
        self.start_time = datetime.now(timezone.utc)
        try:
            self.load_scenario(scenario_path)

            # Setup components
            self.setup_chaos(self.service_bus)

            # Run steps
            self.run_steps()

        except Exception as e:
            logger.error(f"❌ Scenario failed with error: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

        finally:
            self.teardown()
            self.end_time = datetime.now(timezone.utc)

        # Generate results
        return self._generate_results()

    def _generate_results(self) -> Dict[str, Any]:
        """Generate test results summary"""
        duration = (self.end_time - self.start_time).total_seconds()

        all_passed = all(r.passed for r in self.assertion_results)

        results = {
            "scenario": {
                "name": self.scenario.name,
                "description": self.scenario.description
            },
            "status": "passed" if all_passed else "failed",
            "duration_seconds": duration,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "assertions": {
                "total": len(self.assertion_results),
                "passed": sum(1 for r in self.assertion_results if r.passed),
                "failed": sum(1 for r in self.assertion_results if not r.passed),
                "results": [
                    {
                        "name": r.name,
                        "passed": r.passed,
                        "message": r.message,
                        "expected": r.expected,
                        "actual": r.actual
                    }
                    for r in self.assertion_results
                ]
            }
        }

        # Add chaos statistics if available
        if self.chaos_injector:
            results["chaos"] = self.chaos_injector.get_statistics()

        return results


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Scenario Testing Framework")
    parser.add_argument('scenario', type=str, help='Path to scenario YAML file')
    parser.add_argument('--output', type=str, help='Output results to JSON file')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run scenario
    # This CLI is broken due to dependency injection needs.
    # It should be run via the ScenarioTestingServer.
    print("❌ This CLI entrypoint is deprecated. Please use the ScenarioTestingServer.")
    sys.exit(1)

    # Print summary
    print("\n" + "=" * 80)
    print(f"  SCENARIO TEST RESULTS")
    print("=" * 80)
    print(f"  Name: {results['scenario']['name']}")
    print(f"  Status: {'✅ PASSED' if results['status'] == 'passed' else '❌ FAILED'}")
    print(f"  Duration: {results['duration_seconds']:.2f}s")
    print(f"  Assertions: {results['assertions']['passed']}/{results['assertions']['total']} passed")

    if results['status'] == 'failed':
        print("\n  Failed Assertions:")
        for assertion in results['assertions']['results']:
            if not assertion['passed']:
                print(f"    ❌ {assertion['name']}: {assertion['message']}")

    print("=" * 80 + "\n")

    # Save results if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"📄 Results saved to {output_path}\n")

    # Exit with appropriate code
    sys.exit(0 if results['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
