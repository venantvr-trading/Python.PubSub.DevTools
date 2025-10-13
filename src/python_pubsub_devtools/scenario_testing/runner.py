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

# Add tools directories to path
sys.path.insert(0, str(Path(__file__).parent.parent / "mock_exchange"))
sys.path.insert(0, str(Path(__file__).parent.parent / "event_recorder"))
sys.path.insert(0, str(Path(__file__).parent))

# Runtime imports
from .schema import TestScenario
from .chaos_injector import ChaosInjector
from .assertion_checker import AssertionChecker, AssertionResult

# Explicitly import from tools directories
try:
    from python_pubsub_devtools.mock_exchange.scenario_exchange import (
        ScenarioBasedMockExchange,
        MarketScenario
    )
except ImportError:
    # Fallback to relative imports if package not installed
    import sys
    from pathlib import Path

    mock_exchange_path = Path(__file__).parent.parent / "mock_exchange"
    sys.path.insert(0, str(mock_exchange_path))
    from scenario_exchange import ScenarioBasedMockExchange, MarketScenario  # type: ignore

try:
    from python_pubsub_devtools.event_recorder.recorder import EventRecorder
except ImportError:
    # Fallback to relative imports
    import sys
    from pathlib import Path

    event_recorder_path = Path(__file__).parent.parent / "event_recorder"
    sys.path.insert(0, str(event_recorder_path))
    from recorder import EventRecorder  # type: ignore

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScenarioRunner:
    """Runs declarative test scenarios"""

    def __init__(self, scenario_path: str):
        """Initialize scenario runner

        Args:
            scenario_path: Path to YAML scenario file
        """
        self.scenario_path = Path(scenario_path)
        self.scenario: Optional[TestScenario] = None
        self.exchange: Optional[ScenarioBasedMockExchange] = None
        self.recorder: Optional[EventRecorder] = None
        self.chaos_injector: Optional[ChaosInjector] = None
        self.service_bus = None

        # Results
        self.start_time = None
        self.end_time = None
        self.assertion_results: List[AssertionResult] = []
        self.events = []

    def load_scenario(self) -> TestScenario:
        """Load scenario from YAML file"""
        logger.info(f"📖 Loading scenario from {self.scenario_path}")

        with open(self.scenario_path, 'r') as f:
            data = yaml.safe_load(f)

        self.scenario = TestScenario(**data)
        logger.info(f"✅ Loaded scenario: {self.scenario.name}")
        logger.info(f"   {self.scenario.description}")

        return self.scenario

    def setup_exchange(self) -> ScenarioBasedMockExchange:
        """Setup mock exchange based on scenario config"""
        config = self.scenario.setup.exchange

        # Convert scenario name to enum
        try:
            scenario_enum = MarketScenario(config.scenario)
        except ValueError:
            logger.error(f"Unknown scenario: {config.scenario}")
            raise

        logger.info(f"🎰 Setting up exchange with scenario: {config.scenario}")

        self.exchange = ScenarioBasedMockExchange(
            scenario=scenario_enum,
            initial_price=config.initial_price,
            pair=config.pair,
            volatility_multiplier=config.volatility_multiplier,
            spread_bps=config.spread_bps
        )

        return self.exchange

    def setup_recording(self, service_bus):
        """Setup event recording"""
        if not self.scenario.setup.recording or not self.scenario.setup.recording.enabled:
            return None

        config = self.scenario.setup.recording
        session_name = self.scenario.name.lower().replace(" ", "_")

        # Resolve output path template
        output_path = config.output.format(scenario_name=session_name)

        logger.info(f"🎬 Setting up event recording to {output_path}")

        self.recorder = EventRecorder(
            session_name=session_name,
            output_dir=str(Path(output_path).parent)
        )

        self.recorder.start_recording(service_bus)
        return self.recorder

    def setup_chaos(self, service_bus) -> Optional[ChaosInjector]:
        """Setup chaos engineering"""
        if not self.scenario.chaos:
            return None

        logger.info(f"🔥 Setting up chaos engineering with {len(self.scenario.chaos)} actions")

        self.chaos_injector = ChaosInjector(service_bus, self.scenario.chaos)
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

        # Simulate cycles by fetching prices
        for i in range(cycle_count):
            if self.exchange:
                self.exchange.fetch_current_price()
            time.sleep(0.1)  # Small delay between cycles

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

        # Collect events from recorder
        events = self.recorder.events if self.recorder else []

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

        if self.recorder:
            self.recorder.stop_recording()
            self.recorder.save()

    def run(self) -> Dict[str, Any]:
        """Execute complete scenario

        Returns:
            Dict with test results
        """
        self.start_time = datetime.now(timezone.utc)

        try:
            # Load scenario
            self.load_scenario()

            # Setup mock service bus (simplified for testing)
            from unittest.mock import Mock

            self.service_bus = Mock()
            self.service_bus.publish = lambda event_name, event, source: None
            self.service_bus.subscribe = lambda event_name, handler: None

            # Setup components
            self.setup_exchange()
            self.setup_recording(self.service_bus)
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

        # Add exchange statistics if available
        if self.exchange:
            results["exchange"] = self.exchange.get_price_statistics()

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
    runner = ScenarioRunner(args.scenario)
    results = runner.run()

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
