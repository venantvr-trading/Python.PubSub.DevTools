"""
Chaos Engineering Injector

Intercepts service bus to inject failures, delays, and modifications for testing resilience.
"""
import logging
import random
import time
from datetime import datetime, timezone
from typing import Any, Optional, List

from .schema import (
    ChaosAction,
    DelayEventChaos,
    InjectFailureChaos,
    DropEventChaos,
    ModifyEventChaos,
    NetworkLatencyChaos
)

logger = logging.getLogger(__name__)


class ChaosInjector:
    """Intercepts service bus to inject chaos actions"""

    def __init__(self, service_bus, chaos_actions: List[ChaosAction]):
        """Initialize chaos injector

        Args:
            service_bus: The service bus to intercept
            chaos_actions: List of chaos actions to apply
        """
        self.service_bus = service_bus
        self.chaos_actions = chaos_actions
        self._original_publish = None
        self._current_cycle = 0
        self._event_history = []
        self._active_latency = None
        self._latency_end_cycle = None

        # Statistics
        self.stats = {
            "events_delayed": 0,
            "events_dropped": 0,
            "events_modified": 0,
            "failures_injected": 0,
            "total_delay_ms": 0
        }

    def start(self):
        """Start intercepting service bus"""
        logger.info("🔥 Starting chaos injector...")
        self._original_publish = self.service_bus.publish

        def chaos_publish(event_name: str, event: Any, source: str):
            """Intercepted publish with chaos injection"""

            # Track event history
            self._event_history.append({
                "event_name": event_name,
                "timestamp": datetime.now(timezone.utc),
                "cycle": self._current_cycle
            })

            # Update cycle number if this is a cycle start event
            if event_name == "BotMonitoringCycleStarted":
                self._current_cycle = getattr(event, 'cycle_number', self._current_cycle)

            # Apply chaos actions
            should_publish, modified_event = self._apply_chaos(event_name, event, source)

            if not should_publish:
                logger.warning(f"🔥 CHAOS: Dropped event {event_name}")
                self.stats["events_dropped"] += 1
                return

            # Apply network latency if active
            if self._active_latency and self._current_cycle <= self._latency_end_cycle:
                delay_ms = random.randint(
                    self._active_latency.min_delay_ms,
                    self._active_latency.max_delay_ms
                )
                logger.warning(f"🔥 CHAOS: Network latency {delay_ms}ms for {event_name}")
                time.sleep(delay_ms / 1000.0)
                self.stats["total_delay_ms"] += delay_ms

            # Publish (possibly modified) event
            return self._original_publish(event_name, modified_event or event, source)

        self.service_bus.publish = chaos_publish

    def stop(self):
        """Stop intercepting and restore original publish"""
        if self._original_publish:
            logger.info("🔥 Stopping chaos injector...")
            self.service_bus.publish = self._original_publish
            self._original_publish = None

    def _apply_chaos(self, event_name: str, event: Any, source: str) -> tuple[bool, Optional[Any]]:
        """Apply chaos actions to event

        Returns:
            (should_publish, modified_event)
        """
        should_publish = True
        modified_event = None

        for action in self.chaos_actions:
            # Check if action should be applied
            if not self._should_apply_action(action, event_name):
                continue

            if isinstance(action, DelayEventChaos):
                should_publish, modified_event = self._apply_delay(action, event_name, event)

            elif isinstance(action, InjectFailureChaos):
                self._apply_failure_injection(action, event_name, event, source)

            elif isinstance(action, DropEventChaos):
                should_publish = self._apply_drop(action, event_name)

            elif isinstance(action, ModifyEventChaos):
                modified_event = self._apply_modification(action, event_name, event)

            elif isinstance(action, NetworkLatencyChaos):
                self._apply_network_latency(action)

        return should_publish, modified_event

    def _should_apply_action(self, action: ChaosAction, event_name: str) -> bool:
        """Check if chaos action should be applied"""

        # Check event name match
        if hasattr(action, 'event') and action.event != event_name:
            return False

        # Check cycle condition
        if hasattr(action, 'at_cycle') and action.at_cycle is not None:
            if self._current_cycle != action.at_cycle:
                return False

        # Check after_event condition
        if hasattr(action, 'after_event') and action.after_event is not None:
            # Check if after_event has occurred
            recent_events = [e['event_name'] for e in self._event_history[-10:]]
            if action.after_event not in recent_events:
                return False

        return True

    def _apply_delay(self, action: DelayEventChaos, event_name: str, event: Any) -> tuple[bool, None]:
        """Apply event delay"""
        delay_seconds = action.delay_ms / 1000.0
        logger.warning(f"🔥 CHAOS: Delaying {event_name} by {action.delay_ms}ms")
        time.sleep(delay_seconds)
        self.stats["events_delayed"] += 1
        self.stats["total_delay_ms"] += action.delay_ms
        return True, None

    def _apply_failure_injection(self, action: InjectFailureChaos, event_name: str, event: Any, source: str):
        """Inject a failure event"""
        logger.warning(f"🔥 CHAOS: Injecting failure event {action.event}")

        # Dynamically import the failed event class
        try:
            import sys
            from pathlib import Path

            # Add project root to path if not already
            project_root = Path(__file__).parent.parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            # Try to import from python_pubsub_devtools events (if available)
            try:
                from python_pubsub_devtools import events as events_module

                failed_event_class = getattr(events_module, action.event, None)
            except (ImportError, AttributeError):
                # Fallback: create a generic failed event
                failed_event_class = None

            if not failed_event_class:
                logger.warning(f"Failed event class {action.event} not found, creating generic failure")
                # Create a generic Pydantic event
                from pydantic import BaseModel

                class GenericFailedEvent(BaseModel):
                    cycle_id: int
                    error_message: str
                    timestamp: str

                failed_event_class = GenericFailedEvent

            # Extract cycle_id from original event if available
            cycle_id = getattr(event, 'cycle_id', self._current_cycle)

            # Create failed event instance
            failed_event = failed_event_class(
                cycle_id=cycle_id,
                error_message=action.error_message,
                timestamp=datetime.now(timezone.utc).isoformat()
            )

            # Publish the failure
            self._original_publish(action.event, failed_event, "ChaosInjector")
            self.stats["failures_injected"] += 1

        except Exception as e:
            logger.error(f"Failed to inject failure event: {e}")

    def _apply_drop(self, action: DropEventChaos, event_name: str) -> bool:
        """Drop event based on probability"""
        if random.random() < action.probability:
            logger.warning(f"🔥 CHAOS: Dropping event {event_name}")
            self.stats["events_dropped"] += 1
            return False
        return True

    def _apply_modification(self, action: ModifyEventChaos, event_name: str, event: Any) -> Any:
        """Modify event data"""
        if not hasattr(event, action.field):
            logger.warning(f"Event {event_name} has no field {action.field}")
            return event

        logger.warning(f"🔥 CHAOS: Modifying {event_name}.{action.field} to {action.value}")

        # Create a modified copy
        if hasattr(event, 'model_copy'):
            # Pydantic model
            modified = event.model_copy(update={action.field: action.value})
        else:
            # Regular object - create shallow copy and modify
            import copy

            modified = copy.copy(event)
            setattr(modified, action.field, action.value)

        self.stats["events_modified"] += 1
        return modified

    def _apply_network_latency(self, action: NetworkLatencyChaos):
        """Enable network latency for duration"""
        if action.at_cycle is not None and self._current_cycle == action.at_cycle:
            logger.warning(
                f"🔥 CHAOS: Enabling network latency {action.min_delay_ms}-{action.max_delay_ms}ms "
                f"for {action.duration_cycles} cycles"
            )
            self._active_latency = action
            self._latency_end_cycle = self._current_cycle + action.duration_cycles

    def get_statistics(self) -> dict:
        """Get chaos injection statistics"""
        return {
            **self.stats,
            "total_events": len(self._event_history),
            "current_cycle": self._current_cycle
        }

    def __enter__(self):
        """Context manager support"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.stop()
        return False
