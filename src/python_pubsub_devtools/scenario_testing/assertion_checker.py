"""
Assertion Checker - Validates scenario assertions against recorded events.
"""
from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import Any, Dict, List

from .scenario_schema import Assertion, AssertionType


@dataclass
class AssertionResult:
    """
    Result of an assertion check.

    Attributes:
        assertion: The assertion that was checked
        passed: Whether the assertion passed
        actual_value: Actual value observed
        expected_value: Expected value
        message: Human-readable result message
    """
    assertion: Assertion
    passed: bool
    actual_value: Any
    expected_value: Any
    message: str


class AssertionChecker:
    """
    Checks assertions against recorded events.

    Validates event counts, field values, and absence of events based on
    declarative assertions defined in test scenarios.
    """

    OPERATORS = {
        "==": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "contains": lambda a, b: b in a,
        "not_contains": lambda a, b: b not in a,
    }

    def __init__(self):
        """Initialize assertion checker"""
        self.recorded_events: List[Dict[str, Any]] = []

    def record_event(self, event_name: str, event_data: Any) -> None:
        """
        Record an event for later assertion checking.

        Args:
            event_name: Name of the event
            event_data: Event data (dict or object)
        """
        # Convert event_data to dict if it's an object
        if hasattr(event_data, '__dict__'):
            data = event_data.__dict__
        elif hasattr(event_data, 'model_dump'):
            data = event_data.model_dump()
        elif isinstance(event_data, dict):
            data = event_data
        else:
            data = {'value': event_data}

        self.recorded_events.append({
            'event_name': event_name,
            'event_data': data
        })

    def check_assertion(self, assertion: Assertion) -> AssertionResult:
        """
        Check a single assertion against recorded events.

        Args:
            assertion: Assertion to check

        Returns:
            AssertionResult with check outcome
        """
        if assertion.type == AssertionType.EVENT_COUNT:
            return self._check_event_count(assertion)
        elif assertion.type == AssertionType.EVENT_VALUE:
            return self._check_event_value(assertion)
        elif assertion.type == AssertionType.NO_EVENT:
            return self._check_no_event(assertion)
        else:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                actual_value=None,
                expected_value=None,
                message=f"Unknown assertion type: {assertion.type}"
            )

    def _check_event_count(self, assertion: Assertion) -> AssertionResult:
        """Check event count assertion"""
        matching_events = [
            e for e in self.recorded_events
            if e['event_name'] == assertion.event_name
        ]
        actual_count = len(matching_events)
        expected_count = assertion.expected_count

        passed = actual_count == expected_count
        message = (
            f"Event '{assertion.event_name}' count: {actual_count} "
            f"(expected {expected_count})"
        )

        return AssertionResult(
            assertion=assertion,
            passed=passed,
            actual_value=actual_count,
            expected_value=expected_count,
            message=message
        )

    def _check_event_value(self, assertion: Assertion) -> AssertionResult:
        """Check event value assertion"""
        matching_events = [
            e for e in self.recorded_events
            if e['event_name'] == assertion.event_name
        ]

        if not matching_events:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                actual_value=None,
                expected_value=assertion.expected_value,
                message=f"Event '{assertion.event_name}' not found"
            )

        # Get value from first matching event using field path
        event_data = matching_events[0]['event_data']
        actual_value = self._get_field_value(event_data, assertion.field_path)

        # Compare using operator
        op_func = self.OPERATORS.get(assertion.operator, operator.eq)
        passed = op_func(actual_value, assertion.expected_value)

        message = (
            f"Event '{assertion.event_name}'.{assertion.field_path}: "
            f"{actual_value} {assertion.operator} {assertion.expected_value} "
            f"({'PASS' if passed else 'FAIL'})"
        )

        return AssertionResult(
            assertion=assertion,
            passed=passed,
            actual_value=actual_value,
            expected_value=assertion.expected_value,
            message=message
        )

    def _check_no_event(self, assertion: Assertion) -> AssertionResult:
        """Check that event did NOT occur"""
        matching_events = [
            e for e in self.recorded_events
            if e['event_name'] == assertion.event_name
        ]
        actual_count = len(matching_events)
        passed = actual_count == 0

        message = (
            f"Event '{assertion.event_name}' should not occur "
            f"(found {actual_count} occurrences)"
        )

        return AssertionResult(
            assertion=assertion,
            passed=passed,
            actual_value=actual_count,
            expected_value=0,
            message=message
        )

    def _get_field_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """
        Get nested field value using dot-separated path.

        Args:
            data: Dict containing event data
            field_path: Dot-separated path (e.g., "price" or "order.quantity")

        Returns:
            Field value or None if not found
        """
        if not field_path:
            return data

        parts = field_path.split('.')
        value = data

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

            if value is None:
                break

        return value

    def check_all_assertions(self, assertions: List[Assertion]) -> List[AssertionResult]:
        """
        Check all assertions and return results.

        Args:
            assertions: List of assertions to check

        Returns:
            List of AssertionResults
        """
        return [self.check_assertion(a) for a in assertions]

    def clear(self) -> None:
        """Clear recorded events"""
        self.recorded_events.clear()
