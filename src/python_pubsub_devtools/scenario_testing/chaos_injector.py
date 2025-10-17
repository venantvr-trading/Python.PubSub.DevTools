"""
Chaos Injector - Injects failures, delays, and drops into event bus for testing.
"""
from __future__ import annotations

import fnmatch
import logging
import random
import time
from types import SimpleNamespace
from typing import Any, Callable, Dict, Optional

from .scenario_schema import ChaosAction, ChaosType

logger = logging.getLogger(__name__)


class ChaosInjector:
    """
    Injects chaos into ServiceBus for testing resilience.

    Supports:
    - Failures: Raise exceptions
    - Delays: Add delays before event publication
    - Drops: Silently drop events
    - Latency: Add random latency

    Zero-coupling design: Works with any ServiceBus without requiring
    application event classes.
    """

    def __init__(self, service_bus: Any, event_registry: Optional[Dict[str, type]] = None):
        """
        Initialize chaos injector.

        Args:
            service_bus: ServiceBus instance to inject chaos into
            event_registry: Optional dict mapping event names to event classes
                          (enables reconstruction of actual event objects)
        """
        self.service_bus = service_bus
        self.event_registry = event_registry or {}
        self._original_publish: Optional[Callable] = None
        self._active_chaos: list[ChaosAction] = []
        self._start_time: float = 0

    def start(self, chaos_actions: list[ChaosAction]) -> None:
        """
        Start chaos injection by monkey-patching ServiceBus.publish.

        Args:
            chaos_actions: List of chaos actions to inject
        """
        if self._original_publish:
            logger.warning("Chaos injector already started")
            return

        self._active_chaos = chaos_actions
        self._start_time = time.time()
        self._original_publish = self.service_bus.publish

        def chaos_publish(event_name: str, event: Any, source: str):
            """Wrapped publish with chaos injection"""
            # Check if any chaos action applies
            for chaos in self._active_chaos:
                if self._should_apply_chaos(event_name, chaos):
                    self._apply_chaos(event_name, event, source, chaos)
                    return  # Chaos applied, don't call original

            # No chaos applied, call original
            return self._original_publish(event_name, event, source)

        self.service_bus.publish = chaos_publish
        logger.info(f"Chaos injector started with {len(chaos_actions)} action(s)")

    def stop(self) -> None:
        """Stop chaos injection and restore original publish"""
        if self._original_publish:
            self.service_bus.publish = self._original_publish
            self._original_publish = None
            logger.info("Chaos injector stopped")

    def _should_apply_chaos(self, event_name: str, chaos: ChaosAction) -> bool:
        """
        Check if chaos should be applied to this event.

        Args:
            event_name: Name of the event
            chaos: Chaos action

        Returns:
            True if chaos should be applied
        """
        # Check duration (0 = entire scenario)
        if chaos.duration_ms > 0:
            elapsed_ms = (time.time() - self._start_time) * 1000
            if elapsed_ms > chaos.duration_ms:
                return False

        # Check event name match (supports wildcards)
        if not fnmatch.fnmatch(event_name, chaos.target_event):
            return False

        # Check probability
        if random.random() > chaos.probability:
            return False

        return True

    def _apply_chaos(self, event_name: str, event: Any, source: str, chaos: ChaosAction) -> None:
        """
        Apply chaos action.

        Args:
            event_name: Event name
            event: Event data
            source: Event source
            chaos: Chaos action to apply
        """
        if chaos.type == ChaosType.FAILURE:
            self._inject_failure(event_name, chaos)
        elif chaos.type == ChaosType.DELAY:
            self._inject_delay(event_name, event, source, chaos)
        elif chaos.type == ChaosType.DROP:
            self._inject_drop(event_name)
        elif chaos.type == ChaosType.LATENCY:
            self._inject_latency(event_name, event, source, chaos)

    def _inject_failure(self, event_name: str, chaos: ChaosAction) -> None:
        """Inject failure (raise exception)"""
        error_msg = chaos.error_message or f"Chaos: {event_name} failed"
        logger.info(f"🔥 Chaos FAILURE: {event_name} - {error_msg}")
        raise RuntimeError(error_msg)

    def _inject_delay(self, event_name: str, event: Any, source: str, chaos: ChaosAction) -> None:
        """Inject delay before publishing"""
        delay_sec = (chaos.delay_ms or 1000) / 1000.0
        logger.info(f"⏱️  Chaos DELAY: {event_name} delayed by {delay_sec}s")
        time.sleep(delay_sec)
        # Publish after delay
        self._original_publish(event_name, event, source)

    def _inject_drop(self, event_name: str) -> None:
        """Drop event (don't publish)"""
        logger.info(f"🗑️  Chaos DROP: {event_name} dropped")
        # Do nothing - event is dropped

    def _inject_latency(self, event_name: str, event: Any, source: str, chaos: ChaosAction) -> None:
        """Inject random latency"""
        max_delay_ms = chaos.delay_ms or 500
        delay_sec = random.uniform(0, max_delay_ms) / 1000.0
        logger.info(f"🐌 Chaos LATENCY: {event_name} delayed by {delay_sec:.3f}s")
        time.sleep(delay_sec)
        # Publish after latency
        self._original_publish(event_name, event, source)

    def create_event_from_data(self, event_name: str, event_data: Dict[str, Any]) -> Any:
        """
        Create event instance from data.

        If event_registry contains the event class, use it.
        Otherwise, create a SimpleNamespace (zero-coupling).

        Args:
            event_name: Event name
            event_data: Event data as dict

        Returns:
            Event instance (class or SimpleNamespace)
        """
        event_class = self.event_registry.get(event_name)

        if event_class:
            # Use registered event class
            try:
                if hasattr(event_class, 'model_validate'):
                    # Pydantic model
                    return event_class.model_validate(event_data)
                else:
                    # Regular class
                    return event_class(**event_data)
            except Exception as e:
                logger.warning(f"Failed to create {event_name} instance: {e}, using SimpleNamespace")
                return SimpleNamespace(**event_data)
        else:
            # Zero-coupling: use SimpleNamespace
            return SimpleNamespace(**event_data)

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.stop()
