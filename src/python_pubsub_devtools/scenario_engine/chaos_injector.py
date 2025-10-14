"""
Generic Chaos Injector

Injects chaos into event-driven systems for resilience testing.
Completely domain-agnostic - works with any event bus.
"""
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ChaosAction(ABC):
    """Base class for chaos engineering actions"""

    @abstractmethod
    def should_apply(self, event_name: str, cycle_count: int, last_event: Optional[str]) -> bool:
        """Determine if this chaos action should be applied

        Args:
            event_name: Name of the current event
            cycle_count: Current cycle number
            last_event: Name of the last event that occurred

        Returns:
            True if action should be applied
        """
        pass

    @abstractmethod
    def apply(self, event_name: str, event_data: Any, publish_fn: Callable) -> bool:
        """Apply the chaos action

        Args:
            event_name: Name of the event
            event_data: Event data
            publish_fn: Function to publish events

        Returns:
            True if event should continue normal flow, False if it was modified/dropped
        """
        pass


@dataclass
class DelayEvent(ChaosAction):
    """Delay publication of an event"""
    event_pattern: str  # Event name or pattern to match
    delay_ms: int  # Delay in milliseconds
    at_cycle: Optional[int] = None  # Apply at specific cycle
    after_event: Optional[str] = None  # Apply after specific event
    probability: float = 1.0  # Probability of applying (0.0-1.0)

    def should_apply(self, event_name: str, cycle_count: int, last_event: Optional[str]) -> bool:
        """Check if delay should be applied"""
        # Check event name match
        if self.event_pattern not in event_name:
            return False

        # Check cycle constraint
        if self.at_cycle is not None and cycle_count != self.at_cycle:
            return False

        # Check after_event constraint
        if self.after_event is not None and last_event != self.after_event:
            return False

        # Check probability
        if random.random() > self.probability:
            return False

        return True

    def apply(self, event_name: str, event_data: Any, publish_fn: Callable) -> bool:
        """Delay the event"""
        print(f"⏱️  [CHAOS] Delaying {event_name} by {self.delay_ms}ms")
        time.sleep(self.delay_ms / 1000.0)
        return True  # Continue normal flow after delay


@dataclass
class DropEvent(ChaosAction):
    """Drop (don't publish) an event"""
    event_pattern: str  # Event name or pattern to match
    at_cycle: Optional[int] = None
    after_event: Optional[str] = None
    probability: float = 1.0

    def should_apply(self, event_name: str, cycle_count: int, last_event: Optional[str]) -> bool:
        """Check if event should be dropped"""
        if self.event_pattern not in event_name:
            return False

        if self.at_cycle is not None and cycle_count != self.at_cycle:
            return False

        if self.after_event is not None and last_event != self.after_event:
            return False

        if random.random() > self.probability:
            return False

        return True

    def apply(self, event_name: str, event_data: Any, publish_fn: Callable) -> bool:
        """Drop the event"""
        print(f"🗑️  [CHAOS] Dropping {event_name}")
        return False  # Don't continue normal flow


@dataclass
class ModifyEvent(ChaosAction):
    """Modify event data"""
    event_pattern: str
    field_path: str  # Dot-notation path to field (e.g., "price.value")
    new_value: Any  # New value to set
    at_cycle: Optional[int] = None
    after_event: Optional[str] = None
    probability: float = 1.0

    def should_apply(self, event_name: str, cycle_count: int, last_event: Optional[str]) -> bool:
        """Check if event should be modified"""
        if self.event_pattern not in event_name:
            return False

        if self.at_cycle is not None and cycle_count != self.at_cycle:
            return False

        if self.after_event is not None and last_event != self.after_event:
            return False

        if random.random() > self.probability:
            return False

        return True

    def apply(self, event_name: str, event_data: Any, publish_fn: Callable) -> bool:
        """Modify the event data"""
        try:
            # Navigate to field using dot notation
            parts = self.field_path.split('.')
            obj = event_data

            # Navigate to parent
            for part in parts[:-1]:
                if hasattr(obj, part):
                    obj = getattr(obj, part)
                elif isinstance(obj, dict):
                    obj = obj[part]
                else:
                    raise AttributeError(f"Cannot navigate to {part}")

            # Set final value
            final_part = parts[-1]
            if hasattr(obj, final_part):
                setattr(obj, final_part, self.new_value)
            elif isinstance(obj, dict):
                obj[final_part] = self.new_value
            else:
                raise AttributeError(f"Cannot set {final_part}")

            print(f"✏️  [CHAOS] Modified {event_name}.{self.field_path} = {self.new_value}")
        except Exception as e:
            print(f"⚠️  [CHAOS] Failed to modify {event_name}: {e}")

        return True  # Continue normal flow


@dataclass
class InjectFailureEvent(ChaosAction):
    """Inject a failure event"""
    trigger_pattern: str  # Event that triggers the injection
    failure_event_name: str  # Name of failure event to inject
    failure_data: Optional[Dict[str, Any]] = None  # Data for failure event
    at_cycle: Optional[int] = None
    after_event: Optional[str] = None
    probability: float = 1.0

    def should_apply(self, event_name: str, cycle_count: int, last_event: Optional[str]) -> bool:
        """Check if failure should be injected"""
        if self.trigger_pattern not in event_name:
            return False

        if self.at_cycle is not None and cycle_count != self.at_cycle:
            return False

        if self.after_event is not None and last_event != self.after_event:
            return False

        if random.random() > self.probability:
            return False

        return True

    def apply(self, event_name: str, event_data: Any, publish_fn: Callable) -> bool:
        """Inject failure event"""
        print(f"💥 [CHAOS] Injecting {self.failure_event_name} (triggered by {event_name})")

        # Publish failure event
        failure_data = self.failure_data or {"error": "Chaos engineering injected failure"}
        publish_fn(self.failure_event_name, failure_data, "ChaosInjector")

        return True  # Allow original event to continue


class ChaosInjector:
    """Generic chaos injector for event-driven systems

    Usage:
        chaos = ChaosInjector()
        chaos.add_action(DelayEvent("PriceFetched", delay_ms=5000, at_cycle=10))
        chaos.add_action(DropEvent("IndicatorsCalculated", probability=0.1))

        chaos.wrap_service_bus(service_bus)
        # ... run your system ...
        chaos.unwrap_service_bus()
    """

    def __init__(self):
        """Initialize chaos injector"""
        self.actions: List[ChaosAction] = []
        self.cycle_count = 0
        self.last_event: Optional[str] = None
        self.event_history: List[Dict[str, Any]] = []
        self._original_publish: Optional[Callable] = None
        self._service_bus: Optional[Any] = None

    def add_action(self, action: ChaosAction):
        """Add a chaos action

        Args:
            action: ChaosAction to add
        """
        self.actions.append(action)
        print(f"🎭 [CHAOS] Added action: {action.__class__.__name__}")

    def add_actions(self, actions: List[ChaosAction]):
        """Add multiple chaos actions

        Args:
            actions: List of ChaosAction to add
        """
        for action in actions:
            self.add_action(action)

    def wrap_service_bus(self, service_bus: Any):
        """Wrap a service bus to inject chaos

        Args:
            service_bus: Service bus instance with publish() method
        """
        self._service_bus = service_bus
        self._original_publish = service_bus.publish

        def chaos_publish(event_name: str, event_data: Any, source: str):
            """Wrapped publish with chaos injection"""
            # Record event
            self.event_history.append({
                "event_name": event_name,
                "source": source,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cycle": self.cycle_count
            })

            # Check if we should apply any chaos
            should_publish = True
            for action in self.actions:
                if action.should_apply(event_name, self.cycle_count, self.last_event):
                    result = action.apply(event_name, event_data, self._original_publish)
                    if not result:
                        should_publish = False
                        break

            # Publish if not dropped
            if should_publish:
                self._original_publish(event_name, event_data, source)

            # Update state
            self.last_event = event_name

            # Increment cycle on specific events (configurable)
            if "Completed" in event_name or "Finished" in event_name:
                self.cycle_count += 1

        service_bus.publish = chaos_publish
        print(f"🎭 [CHAOS] Service bus wrapped with {len(self.actions)} chaos actions")

    def unwrap_service_bus(self):
        """Remove chaos wrapper and restore original publish"""
        if self._service_bus and self._original_publish:
            self._service_bus.publish = self._original_publish
            print(f"✅ [CHAOS] Service bus unwrapped. {len(self.event_history)} events recorded.")

    def get_statistics(self) -> Dict[str, Any]:
        """Get chaos injection statistics

        Returns:
            Dict with statistics about chaos actions applied
        """
        from collections import Counter

        event_counts = Counter(e["event_name"] for e in self.event_history)

        return {
            "total_events": len(self.event_history),
            "total_cycles": self.cycle_count,
            "chaos_actions": len(self.actions),
            "event_counts": dict(event_counts.most_common(10))
        }

    def reset(self):
        """Reset chaos injector state"""
        self.cycle_count = 0
        self.last_event = None
        self.event_history = []
        print("🔄 [CHAOS] Injector reset")
