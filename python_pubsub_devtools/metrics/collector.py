"""
Event Metrics Collector

Collecte des métriques simples mais puissantes pour les événements.
"""
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter as CounterCollection
from functools import wraps
import statistics


@dataclass
class MetricValue:
    """Valeur d'une métrique avec timestamp"""
    value: float
    timestamp: datetime = field(default_factory=datetime.now)


class Counter:
    """Compteur simple pour événements"""

    def __init__(self):
        self._counts: Dict[str, int] = defaultdict(int)

    def inc(self, label: str, amount: int = 1):
        """Incrémenter le compteur"""
        self._counts[label] += amount

    def get(self, label: str) -> int:
        """Obtenir la valeur du compteur"""
        return self._counts.get(label, 0)

    def get_all(self) -> Dict[str, int]:
        """Obtenir tous les compteurs"""
        return dict(self._counts)

    def reset(self):
        """Réinitialiser tous les compteurs"""
        self._counts.clear()


class Histogram:
    """Histogram pour distribution de valeurs"""

    def __init__(self, max_samples: int = 10000):
        self._samples: Dict[str, List[float]] = defaultdict(list)
        self._max_samples = max_samples

    def observe(self, label: str, value: float):
        """Observer une valeur"""
        samples = self._samples[label]
        samples.append(value)

        # Limit sample size to avoid memory issues
        if len(samples) > self._max_samples:
            samples.pop(0)

    def get_percentile(self, label: str, percentile: float) -> Optional[float]:
        """Obtenir un percentile (0.0 - 1.0)"""
        samples = self._samples.get(label, [])
        if not samples:
            return None

        sorted_samples = sorted(samples)
        index = int(len(sorted_samples) * percentile)
        return sorted_samples[min(index, len(sorted_samples) - 1)]

    def get_average(self, label: str) -> Optional[float]:
        """Obtenir la moyenne"""
        samples = self._samples.get(label, [])
        if not samples:
            return None
        return statistics.mean(samples)

    def get_summary(self, label: str) -> Optional[Dict[str, float]]:
        """Obtenir un résumé statistique"""
        samples = self._samples.get(label, [])
        if not samples:
            return None

        return {
            'count': len(samples),
            'min': min(samples),
            'max': max(samples),
            'avg': statistics.mean(samples),
            'p50': self.get_percentile(label, 0.50),
            'p95': self.get_percentile(label, 0.95),
            'p99': self.get_percentile(label, 0.99),
        }

    def reset(self):
        """Réinitialiser toutes les observations"""
        self._samples.clear()


class EventMetricsCollector:
    """
    Collecteur de métriques pour événements.

    Features:
    - Comptage d'événements par type
    - Histogrammes de temps de traitement
    - Taux d'erreur
    - Top événements
    """

    def __init__(self):
        self.events_published = Counter()
        self.events_processed = Counter()
        self.events_failed = Counter()
        self.processing_time = Histogram()
        self.handler_execution = Histogram()

        self._start_time = datetime.now()
        self._event_timestamps: List[datetime] = []

    def record_event_published(self, event_name: str):
        """Enregistrer un événement publié"""
        self.events_published.inc(event_name)
        self._event_timestamps.append(datetime.now())

    def record_event_processed(self, event_name: str, duration_ms: float):
        """Enregistrer un événement traité"""
        self.events_processed.inc(event_name)
        self.processing_time.observe(event_name, duration_ms)

    def record_event_failed(self, event_name: str, duration_ms: Optional[float] = None):
        """Enregistrer un événement en échec"""
        self.events_failed.inc(event_name)
        if duration_ms is not None:
            self.processing_time.observe(f"{event_name}_failed", duration_ms)

    def record_handler_execution(self, handler_name: str, event_name: str, duration_ms: float, success: bool = True):
        """Enregistrer l'exécution d'un handler"""
        label = f"{handler_name}:{event_name}"
        self.handler_execution.observe(label, duration_ms)

        if success:
            self.events_processed.inc(event_name)
        else:
            self.events_failed.inc(event_name)

    def get_event_rate(self, window_seconds: int = 60) -> float:
        """Calculer le taux d'événements (events/sec)"""
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        recent_events = [ts for ts in self._event_timestamps if ts >= cutoff]

        if not recent_events or window_seconds == 0:
            return 0.0

        return len(recent_events) / window_seconds

    def _calculate_error_rate(self) -> float:
        """Calculer le taux d'erreur global"""
        total_processed = sum(self.events_processed.get_all().values())
        total_failed = sum(self.events_failed.get_all().values())

        total = total_processed + total_failed
        if total == 0:
            return 0.0

        return (total_failed / total) * 100

    def _calculate_avg_time(self) -> float:
        """Calculer le temps de traitement moyen"""
        all_samples = []
        for label in self.processing_time._samples.keys():
            all_samples.extend(self.processing_time._samples[label])

        if not all_samples:
            return 0.0

        return statistics.mean(all_samples)

    def _get_top_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtenir les événements les plus fréquents"""
        all_events = self.events_published.get_all()
        sorted_events = sorted(all_events.items(), key=lambda x: x[1], reverse=True)

        return [
            {'event_type': event, 'count': count}
            for event, count in sorted_events[:limit]
        ]

    def get_summary(self) -> Dict[str, Any]:
        """
        Obtenir un résumé complet des métriques.

        Returns:
            Dict avec:
            - total_events: nombre total d'événements
            - error_rate: taux d'erreur (%)
            - avg_processing_time_ms: temps moyen de traitement
            - event_rate: événements par seconde
            - top_events: top 10 événements
            - uptime_seconds: durée depuis le démarrage
        """
        uptime = (datetime.now() - self._start_time).total_seconds()

        return {
            'total_events': sum(self.events_published.get_all().values()),
            'total_processed': sum(self.events_processed.get_all().values()),
            'total_failed': sum(self.events_failed.get_all().values()),
            'error_rate': self._calculate_error_rate(),
            'avg_processing_time_ms': self._calculate_avg_time(),
            'event_rate_per_sec': self.get_event_rate(window_seconds=60),
            'top_events': self._get_top_events(10),
            'uptime_seconds': uptime,
            'start_time': self._start_time.isoformat(),
        }

    def get_event_stats(self, event_name: str) -> Optional[Dict[str, Any]]:
        """Obtenir les statistiques pour un événement spécifique"""
        published = self.events_published.get(event_name)
        processed = self.events_processed.get(event_name)
        failed = self.events_failed.get(event_name)

        if published == 0:
            return None

        processing_summary = self.processing_time.get_summary(event_name)

        return {
            'event_type': event_name,
            'published': published,
            'processed': processed,
            'failed': failed,
            'error_rate': (failed / (processed + failed) * 100) if (processed + failed) > 0 else 0.0,
            'processing_time': processing_summary,
        }

    def get_handler_stats(self, handler_name: str) -> Dict[str, Any]:
        """Obtenir les statistiques pour un handler spécifique"""
        # Find all labels that match this handler
        matching_labels = [
            label for label in self.handler_execution._samples.keys()
            if label.startswith(f"{handler_name}:")
        ]

        if not matching_labels:
            return {
                'handler': handler_name,
                'executions': 0,
                'avg_duration_ms': 0.0,
            }

        all_durations = []
        for label in matching_labels:
            all_durations.extend(self.handler_execution._samples[label])

        return {
            'handler': handler_name,
            'executions': len(all_durations),
            'avg_duration_ms': statistics.mean(all_durations) if all_durations else 0.0,
            'min_duration_ms': min(all_durations) if all_durations else 0.0,
            'max_duration_ms': max(all_durations) if all_durations else 0.0,
        }

    def reset(self):
        """Réinitialiser toutes les métriques"""
        self.events_published.reset()
        self.events_processed.reset()
        self.events_failed.reset()
        self.processing_time.reset()
        self.handler_execution.reset()
        self._start_time = datetime.now()
        self._event_timestamps.clear()


# Global collector instance
_global_collector: Optional[EventMetricsCollector] = None


def get_metrics_collector() -> EventMetricsCollector:
    """Obtenir l'instance globale du collecteur de métriques"""
    global _global_collector
    if _global_collector is None:
        _global_collector = EventMetricsCollector()
    return _global_collector


def collect_metrics(func: Callable) -> Callable:
    """
    Décorateur pour collecter automatiquement les métriques d'un handler.

    Usage:
        @collect_metrics
        @event_handler("OrderCreated")
        def handle_order(event):
            process_order(event)
    """
    @wraps(func)
    async def async_wrapper(event, *args, **kwargs):
        collector = get_metrics_collector()
        event_name = event.__class__.__name__ if hasattr(event, '__class__') else 'UnknownEvent'
        handler_name = func.__name__

        start_time = time.time()
        success = True

        try:
            result = await func(event, *args, **kwargs)
            return result
        except Exception as e:
            success = False
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            collector.record_handler_execution(handler_name, event_name, duration_ms, success)

    @wraps(func)
    def sync_wrapper(event, *args, **kwargs):
        collector = get_metrics_collector()
        event_name = event.__class__.__name__ if hasattr(event, '__class__') else 'UnknownEvent'
        handler_name = func.__name__

        start_time = time.time()
        success = True

        try:
            result = func(event, *args, **kwargs)
            return result
        except Exception as e:
            success = False
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            collector.record_handler_execution(handler_name, event_name, duration_ms, success)

    # Return appropriate wrapper based on whether function is async
    if hasattr(func, '__code__') and func.__code__.co_flags & 0x0100:  # CO_COROUTINE
        return async_wrapper
    return sync_wrapper
