"""
Assertion Checker

Validates test assertions against recorded events and system state.
"""
import logging
from collections import Counter
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AssertionResult:
    """Result of an assertion check"""

    def __init__(self, name: str, passed: bool, message: str, expected: Any = None, actual: Any = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.expected = expected
        self.actual = actual

    def __repr__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status}: {self.name} - {self.message}"


class AssertionChecker:
    """Checks assertions against events and state"""

    def __init__(self, events: List[Dict[str, Any]]):
        """Initialize assertion checker

        Args:
            events: List of recorded events with metadata
        """
        self.events = events
        self.event_counts = Counter(e['event_name'] for e in events)
        self.results: List[AssertionResult] = []

    def check_assertions(self, assertions: Dict[str, Any]) -> List[AssertionResult]:
        """Check all assertions

        Args:
            assertions: Dictionary of assertions to check

        Returns:
            List of assertion results
        """
        self.results = []

        for key, value in assertions.items():
            if key == "event_count":
                self._check_event_count(value)
            elif key == "event_sequence":
                self._check_event_sequence(value)
            elif key == "no_panic_sell":
                self._check_no_panic_sell(value)
            elif key == "final_capital":
                self._check_final_capital(value)
            elif key == "position_count":
                self._check_position_count(value)
            elif key == "custom":
                self._check_custom_assertion(value)
            else:
                logger.warning(f"Unknown assertion type: {key}")

        return self.results

    def _check_event_count(self, expected_counts: Dict[str, Dict[str, int]]):
        """Check event counts match expectations

        Args:
            expected_counts: Dict like {"EventName": {"min": 3, "max": 10, "exact": 5}}
        """
        for event_name, constraints in expected_counts.items():
            actual_count = self.event_counts.get(event_name, 0)

            if "exact" in constraints:
                expected = constraints["exact"]
                passed = actual_count == expected
                self.results.append(AssertionResult(
                    name=f"event_count.{event_name}.exact",
                    passed=passed,
                    message=f"Expected exactly {expected} {event_name} events, got {actual_count}",
                    expected=expected,
                    actual=actual_count
                ))

            if "min" in constraints:
                expected = constraints["min"]
                passed = actual_count >= expected
                self.results.append(AssertionResult(
                    name=f"event_count.{event_name}.min",
                    passed=passed,
                    message=f"Expected at least {expected} {event_name} events, got {actual_count}",
                    expected=f">= {expected}",
                    actual=actual_count
                ))

            if "max" in constraints:
                expected = constraints["max"]
                passed = actual_count <= expected
                self.results.append(AssertionResult(
                    name=f"event_count.{event_name}.max",
                    passed=passed,
                    message=f"Expected at most {expected} {event_name} events, got {actual_count}",
                    expected=f"<= {expected}",
                    actual=actual_count
                ))

    def _check_event_sequence(self, expected_sequence: List[str]):
        """Check events occurred in expected sequence

        Args:
            expected_sequence: List of event names in expected order
        """
        actual_sequence = [e['event_name'] for e in self.events]

        # Find subsequence
        seq_index = 0
        for event_name in actual_sequence:
            if seq_index < len(expected_sequence) and event_name == expected_sequence[seq_index]:
                seq_index += 1

        passed = seq_index == len(expected_sequence)
        self.results.append(AssertionResult(
            name="event_sequence",
            passed=passed,
            message=f"Expected sequence {expected_sequence}, found {seq_index}/{len(expected_sequence)} events in order",
            expected=expected_sequence,
            actual=f"{seq_index}/{len(expected_sequence)} matched"
        ))

    def _check_no_panic_sell(self, config: Dict[str, Any]):
        """Check no panic selling during crash period

        Args:
            config: Dict like {"crash_start_cycle": 20, "crash_end_cycle": 30}
        """
        crash_start = config.get("crash_start_cycle", 20)
        crash_end = config.get("crash_end_cycle", 30)

        # Count PositionSold events during crash period
        panic_sells = sum(
            1 for e in self.events
            if e['event_name'] == "PositionSold"
            and crash_start <= e.get('cycle', 0) <= crash_end
        )

        passed = panic_sells == 0
        self.results.append(AssertionResult(
            name="no_panic_sell",
            passed=passed,
            message=f"Expected no sells during crash (cycles {crash_start}-{crash_end}), found {panic_sells}",
            expected=0,
            actual=panic_sells
        ))

    def _check_final_capital(self, constraints: Dict[str, float]):
        """Check final capital is within expected range

        Args:
            constraints: Dict like {"min": 9000.0, "max": 12000.0}
        """
        # Find last CapitalRefreshed event
        capital_events = [e for e in self.events if e['event_name'] == "CapitalRefreshed"]

        if not capital_events:
            self.results.append(AssertionResult(
                name="final_capital",
                passed=False,
                message="No CapitalRefreshed events found",
                expected=constraints,
                actual=None
            ))
            return

        last_capital_event = capital_events[-1]
        final_capital = last_capital_event.get('event_data', {}).get('available_capital', 0)

        passed = True
        messages = []

        if "min" in constraints:
            min_capital = constraints["min"]
            if final_capital < min_capital:
                passed = False
                messages.append(f"below minimum {min_capital}")

        if "max" in constraints:
            max_capital = constraints["max"]
            if final_capital > max_capital:
                passed = False
                messages.append(f"above maximum {max_capital}")

        message = f"Final capital {final_capital:.2f}"
        if messages:
            message += f" ({', '.join(messages)})"

        self.results.append(AssertionResult(
            name="final_capital",
            passed=passed,
            message=message,
            expected=constraints,
            actual=final_capital
        ))

    def _check_position_count(self, constraints: Dict[str, int]):
        """Check number of open positions

        Args:
            constraints: Dict like {"min": 3, "max": 10}
        """
        # Count PositionPurchased - PositionSold
        purchases = self.event_counts.get("PositionPurchased", 0)
        sales = self.event_counts.get("PositionSold", 0)
        open_positions = purchases - sales

        if "min" in constraints:
            min_pos = constraints["min"]
            passed = open_positions >= min_pos
            self.results.append(AssertionResult(
                name="position_count.min",
                passed=passed,
                message=f"Expected at least {min_pos} open positions, got {open_positions}",
                expected=f">= {min_pos}",
                actual=open_positions
            ))

        if "max" in constraints:
            max_pos = constraints["max"]
            passed = open_positions <= max_pos
            self.results.append(AssertionResult(
                name="position_count.max",
                passed=passed,
                message=f"Expected at most {max_pos} open positions, got {open_positions}",
                expected=f"<= {max_pos}",
                actual=open_positions
            ))

    def _check_custom_assertion(self, custom_func):
        """Check custom assertion function

        Args:
            custom_func: Callable that takes events and returns (passed, message)
        """
        try:
            passed, message = custom_func(self.events)
            self.results.append(AssertionResult(
                name="custom",
                passed=passed,
                message=message
            ))
        except Exception as e:
            self.results.append(AssertionResult(
                name="custom",
                passed=False,
                message=f"Custom assertion failed: {str(e)}"
            ))

    def all_passed(self) -> bool:
        """Check if all assertions passed"""
        return all(r.passed for r in self.results)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of assertion results"""
        return {
            "total": len(self.results),
            "passed": sum(1 for r in self.results if r.passed),
            "failed": sum(1 for r in self.results if not r.passed),
            "pass_rate": sum(1 for r in self.results if r.passed) / len(self.results) if self.results else 0,
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "expected": r.expected,
                    "actual": r.actual
                }
                for r in self.results
            ]
        }
