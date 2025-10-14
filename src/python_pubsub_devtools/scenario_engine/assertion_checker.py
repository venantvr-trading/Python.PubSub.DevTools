"""
Generic Assertion Checker

Validates conditions on event streams - completely domain-agnostic.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from collections import Counter


@dataclass
class AssertionResult:
    """Result of an assertion check"""
    name: str  # Assertion name
    passed: bool  # Did it pass?
    message: str  # Human-readable message
    expected: Any = None  # Expected value
    actual: Any = None  # Actual value
    details: Dict[str, Any] = None  # Additional details

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class Assertion(ABC):
    """Base class for assertions"""

    def __init__(self, name: str):
        """Initialize assertion

        Args:
            name: Unique name for this assertion
        """
        self.name = name

    @abstractmethod
    def check(self, events: List[Dict[str, Any]], context: Dict[str, Any]) -> AssertionResult:
        """Check the assertion

        Args:
            events: List of recorded events
            context: Additional context (e.g., initial state, config)

        Returns:
            AssertionResult with pass/fail status
        """
        pass


class EventCountAssertion(Assertion):
    """Assert that an event occurred a specific number of times"""

    def __init__(self, event_name: str, min_count: Optional[int] = None,
                 max_count: Optional[int] = None, exact_count: Optional[int] = None):
        """Initialize event count assertion

        Args:
            event_name: Name of event to count
            min_count: Minimum expected occurrences
            max_count: Maximum expected occurrences
            exact_count: Exact expected occurrences
        """
        super().__init__(f"event_count.{event_name}")
        self.event_name = event_name
        self.min_count = min_count
        self.max_count = max_count
        self.exact_count = exact_count

    def check(self, events: List[Dict[str, Any]], context: Dict[str, Any]) -> AssertionResult:
        """Check event count"""
        count = sum(1 for e in events if e.get("event_name") == self.event_name)

        if self.exact_count is not None:
            passed = count == self.exact_count
            return AssertionResult(
                name=self.name,
                passed=passed,
                message=f"Expected exactly {self.exact_count} {self.event_name} events, got {count}",
                expected=self.exact_count,
                actual=count
            )

        messages = []
        passed = True

        if self.min_count is not None:
            if count < self.min_count:
                passed = False
                messages.append(f"Expected at least {self.min_count}, got {count}")

        if self.max_count is not None:
            if count > self.max_count:
                passed = False
                messages.append(f"Expected at most {self.max_count}, got {count}")

        if not passed:
            message = f"{self.event_name}: {'; '.join(messages)}"
        else:
            message = f"{self.event_name} occurred {count} times (OK)"

        return AssertionResult(
            name=self.name,
            passed=passed,
            message=message,
            expected=f"{self.min_count}-{self.max_count}" if self.min_count and self.max_count else None,
            actual=count
        )


class EventSequenceAssertion(Assertion):
    """Assert that events occurred in a specific order"""

    def __init__(self, expected_sequence: List[str], allow_gaps: bool = True):
        """Initialize event sequence assertion

        Args:
            expected_sequence: Expected event names in order
            allow_gaps: Allow other events between sequence events
        """
        super().__init__(f"event_sequence.{len(expected_sequence)}_events")
        self.expected_sequence = expected_sequence
        self.allow_gaps = allow_gaps

    def check(self, events: List[Dict[str, Any]], context: Dict[str, Any]) -> AssertionResult:
        """Check event sequence"""
        if self.allow_gaps:
            # Extract matching events
            matching_events = [e for e in events if e.get("event_name") in self.expected_sequence]
            actual_sequence = [e.get("event_name") for e in matching_events]
        else:
            # All events must match
            actual_sequence = [e.get("event_name") for e in events]

        # Check if expected sequence is a subsequence of actual
        expected_idx = 0
        for event_name in actual_sequence:
            if expected_idx < len(self.expected_sequence) and event_name == self.expected_sequence[expected_idx]:
                expected_idx += 1

        passed = expected_idx == len(self.expected_sequence)

        return AssertionResult(
            name=self.name,
            passed=passed,
            message=f"Expected sequence {self.expected_sequence}, got {actual_sequence[:len(self.expected_sequence)]}",
            expected=self.expected_sequence,
            actual=actual_sequence
        )


class NoEventAssertion(Assertion):
    """Assert that a specific event did NOT occur"""

    def __init__(self, event_name: str, during_window: Optional[tuple] = None):
        """Initialize no-event assertion

        Args:
            event_name: Event that should NOT occur
            during_window: Optional (start_cycle, end_cycle) window
        """
        super().__init__(f"no_event.{event_name}")
        self.event_name = event_name
        self.during_window = during_window

    def check(self, events: List[Dict[str, Any]], context: Dict[str, Any]) -> AssertionResult:
        """Check that event did not occur"""
        if self.during_window:
            start_cycle, end_cycle = self.during_window
            matching_events = [
                e for e in events
                if e.get("event_name") == self.event_name
                   and start_cycle <= e.get("cycle", 0) <= end_cycle
            ]
            message_suffix = f" during cycles {start_cycle}-{end_cycle}"
        else:
            matching_events = [e for e in events if e.get("event_name") == self.event_name]
            message_suffix = ""

        count = len(matching_events)
        passed = count == 0

        return AssertionResult(
            name=self.name,
            passed=passed,
            message=f"Expected no {self.event_name}{message_suffix}, found {count}",
            expected=0,
            actual=count
        )


class CustomAssertion(Assertion):
    """Custom assertion with user-defined check function"""

    def __init__(self, name: str, check_fn: Callable[[List[Dict[str, Any]], Dict[str, Any]], AssertionResult]):
        """Initialize custom assertion

        Args:
            name: Assertion name
            check_fn: Function that performs the check
        """
        super().__init__(name)
        self.check_fn = check_fn

    def check(self, events: List[Dict[str, Any]], context: Dict[str, Any]) -> AssertionResult:
        """Delegate to custom check function"""
        return self.check_fn(events, context)


class AssertionChecker:
    """Generic assertion checker for event-driven systems

    Usage:
        checker = AssertionChecker(events)
        checker.add_assertion(EventCountAssertion("DataFetched", min_count=10))
        checker.add_assertion(EventSequenceAssertion(["Started", "Processing", "Completed"]))

        results = checker.check_all()
        assert checker.all_passed(), f"{checker.failures_summary()}"
    """

    def __init__(self, events: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None):
        """Initialize assertion checker

        Args:
            events: List of recorded events
            context: Optional context dict with additional data
        """
        self.events = events
        self.context = context or {}
        self.assertions: List[Assertion] = []
        self.results: List[AssertionResult] = []

        # Pre-compute event statistics for efficiency
        self.event_counts = Counter(e.get("event_name") for e in events)

    def add_assertion(self, assertion: Assertion):
        """Add an assertion to check

        Args:
            assertion: Assertion instance
        """
        self.assertions.append(assertion)

    def add_assertions(self, assertions: List[Assertion]):
        """Add multiple assertions

        Args:
            assertions: List of Assertion instances
        """
        for assertion in assertions:
            self.add_assertion(assertion)

    def check_all(self) -> List[AssertionResult]:
        """Check all assertions

        Returns:
            List of AssertionResult
        """
        self.results = []
        for assertion in self.assertions:
            result = assertion.check(self.events, self.context)
            self.results.append(result)
        return self.results

    def all_passed(self) -> bool:
        """Check if all assertions passed

        Returns:
            True if all passed, False otherwise
        """
        if not self.results:
            self.check_all()
        return all(r.passed for r in self.results)

    def failures_summary(self) -> str:
        """Get summary of failures

        Returns:
            String with failure details
        """
        if not self.results:
            self.check_all()

        failures = [r for r in self.results if not r.passed]
        if not failures:
            return "All assertions passed ✅"

        lines = [f"\n❌ {len(failures)} assertion(s) failed:"]
        for f in failures:
            lines.append(f"  • {f.name}: {f.message}")
        return "\n".join(lines)

    def get_report(self) -> Dict[str, Any]:
        """Get detailed assertion report

        Returns:
            Dict with assertion results and statistics
        """
        if not self.results:
            self.check_all()

        passed = [r for r in self.results if r.passed]
        failed = [r for r in self.results if not r.passed]

        return {
            "total_assertions": len(self.results),
            "passed": len(passed),
            "failed": len(failed),
            "pass_rate": len(passed) / len(self.results) if self.results else 0,
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "expected": r.expected,
                    "actual": r.actual
                }
                for r in self.results
            ],
            "event_statistics": dict(self.event_counts.most_common())
        }

    def print_report(self):
        """Print human-readable report"""
        if not self.results:
            self.check_all()

        print("\n" + "=" * 80)
        print("ASSERTION REPORT")
        print("=" * 80)

        passed = [r for r in self.results if r.passed]
        failed = [r for r in self.results if not r.passed]

        print(f"\nTotal: {len(self.results)} | Passed: {len(passed)} | Failed: {len(failed)}")

        if failed:
            print("\n❌ Failed Assertions:")
            for f in failed:
                print(f"  • {f.name}")
                print(f"    {f.message}")
                if f.expected is not None:
                    print(f"    Expected: {f.expected}, Actual: {f.actual}")

        if passed:
            print("\n✅ Passed Assertions:")
            for p in passed:
                print(f"  • {p.name}: {p.message}")

        print("\n" + "=" * 80)
