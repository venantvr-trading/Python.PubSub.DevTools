"""
Unit tests for Event Metrics Collector

Tests complets du collecteur de métriques.
"""
import pytest
import time
from unittest.mock import Mock

from python_pubsub_devtools.metrics import (
    EventMetricsCollector,
    Counter,
    Histogram,
    collect_metrics,
    get_metrics_collector,
)


class TestCounter:
    """Tests pour la classe Counter"""

    def test_counter_initialization(self):
        """Test que le compteur s'initialise correctement"""
        counter = Counter()
        assert counter.get('test') == 0

    def test_counter_increment(self):
        """Test l'incrémentation du compteur"""
        counter = Counter()
        counter.inc('orders')
        counter.inc('orders')
        counter.inc('orders')
        assert counter.get('orders') == 3

    def test_counter_increment_with_amount(self):
        """Test l'incrémentation avec un montant spécifique"""
        counter = Counter()
        counter.inc('items', 5)
        counter.inc('items', 3)
        assert counter.get('items') == 8

    def test_counter_multiple_labels(self):
        """Test plusieurs labels différents"""
        counter = Counter()
        counter.inc('orders')
        counter.inc('payments')
        counter.inc('orders')

        assert counter.get('orders') == 2
        assert counter.get('payments') == 1

    def test_counter_get_all(self):
        """Test obtenir tous les compteurs"""
        counter = Counter()
        counter.inc('orders', 5)
        counter.inc('payments', 3)

        all_counts = counter.get_all()
        assert all_counts == {'orders': 5, 'payments': 3}

    def test_counter_reset(self):
        """Test réinitialisation des compteurs"""
        counter = Counter()
        counter.inc('orders', 10)
        counter.reset()
        assert counter.get('orders') == 0


class TestHistogram:
    """Tests pour la classe Histogram"""

    def test_histogram_initialization(self):
        """Test que l'histogramme s'initialise correctement"""
        histogram = Histogram()
        assert histogram.get_average('test') is None

    def test_histogram_observe(self):
        """Test observer une valeur"""
        histogram = Histogram()
        histogram.observe('latency', 10.0)
        histogram.observe('latency', 20.0)
        histogram.observe('latency', 30.0)

        avg = histogram.get_average('latency')
        assert avg == 20.0

    def test_histogram_percentiles(self):
        """Test calcul des percentiles"""
        histogram = Histogram()

        # Add 100 values: 1, 2, 3, ..., 100
        for i in range(1, 101):
            histogram.observe('test', float(i))

        p50 = histogram.get_percentile('test', 0.50)
        p95 = histogram.get_percentile('test', 0.95)
        p99 = histogram.get_percentile('test', 0.99)

        assert 45 <= p50 <= 55  # Around median
        assert 90 <= p95 <= 100  # Around 95th percentile
        assert 95 <= p99 <= 100  # Around 99th percentile

    def test_histogram_summary(self):
        """Test résumé statistique"""
        histogram = Histogram()

        for i in range(1, 11):
            histogram.observe('test', float(i))

        summary = histogram.get_summary('test')

        assert summary is not None
        assert summary['count'] == 10
        assert summary['min'] == 1.0
        assert summary['max'] == 10.0
        assert summary['avg'] == 5.5
        assert summary['p50'] is not None

    def test_histogram_max_samples_limit(self):
        """Test que l'histogramme limite le nombre d'échantillons"""
        histogram = Histogram(max_samples=100)

        # Add 200 samples
        for i in range(200):
            histogram.observe('test', float(i))

        # Should only keep last 100
        samples = histogram._samples['test']
        assert len(samples) == 100

    def test_histogram_empty_label(self):
        """Test comportement avec label vide"""
        histogram = Histogram()
        assert histogram.get_percentile('nonexistent', 0.5) is None
        assert histogram.get_average('nonexistent') is None
        assert histogram.get_summary('nonexistent') is None

    def test_histogram_reset(self):
        """Test réinitialisation de l'histogramme"""
        histogram = Histogram()
        histogram.observe('test', 10.0)
        histogram.reset()
        assert histogram.get_average('test') is None


class TestEventMetricsCollector:
    """Tests pour EventMetricsCollector"""

    def test_collector_initialization(self):
        """Test initialisation du collecteur"""
        collector = EventMetricsCollector()
        assert collector is not None
        assert isinstance(collector.events_published, Counter)
        assert isinstance(collector.processing_time, Histogram)

    def test_record_event_published(self):
        """Test enregistrement d'événement publié"""
        collector = EventMetricsCollector()
        collector.record_event_published('OrderCreated')
        collector.record_event_published('OrderCreated')

        assert collector.events_published.get('OrderCreated') == 2

    def test_record_event_processed(self):
        """Test enregistrement d'événement traité"""
        collector = EventMetricsCollector()
        collector.record_event_processed('OrderCreated', 15.5)

        assert collector.events_processed.get('OrderCreated') == 1
        avg_time = collector.processing_time.get_average('OrderCreated')
        assert avg_time == 15.5

    def test_record_event_failed(self):
        """Test enregistrement d'événement en échec"""
        collector = EventMetricsCollector()
        collector.record_event_failed('PaymentFailed', 25.0)

        assert collector.events_failed.get('PaymentFailed') == 1

    def test_record_handler_execution_success(self):
        """Test enregistrement d'exécution de handler réussie"""
        collector = EventMetricsCollector()
        collector.record_handler_execution('handle_order', 'OrderCreated', 10.0, success=True)

        assert collector.events_processed.get('OrderCreated') == 1
        avg = collector.handler_execution.get_average('handle_order:OrderCreated')
        assert avg == 10.0

    def test_record_handler_execution_failure(self):
        """Test enregistrement d'exécution de handler en échec"""
        collector = EventMetricsCollector()
        collector.record_handler_execution('handle_payment', 'PaymentProcessing', 20.0, success=False)

        assert collector.events_failed.get('PaymentProcessing') == 1

    def test_get_event_rate(self):
        """Test calcul du taux d'événements"""
        collector = EventMetricsCollector()

        # Publish 10 events
        for _ in range(10):
            collector.record_event_published('TestEvent')

        # Rate should be > 0
        rate = collector.get_event_rate(window_seconds=60)
        assert rate > 0

    def test_get_summary(self):
        """Test résumé complet des métriques"""
        collector = EventMetricsCollector()

        collector.record_event_published('OrderCreated')
        collector.record_event_processed('OrderCreated', 10.0)

        collector.record_event_published('PaymentProcessing')
        collector.record_event_failed('PaymentProcessing', 20.0)

        summary = collector.get_summary()

        assert summary['total_events'] == 2
        assert summary['total_processed'] == 1
        assert summary['total_failed'] == 1
        assert summary['error_rate'] == 50.0  # 1 failed out of 2
        assert 'top_events' in summary
        assert 'uptime_seconds' in summary

    def test_get_event_stats(self):
        """Test statistiques pour un événement spécifique"""
        collector = EventMetricsCollector()

        collector.record_event_published('OrderCreated')
        collector.record_event_processed('OrderCreated', 15.0)
        collector.record_event_processed('OrderCreated', 25.0)

        stats = collector.get_event_stats('OrderCreated')

        assert stats is not None
        assert stats['event_type'] == 'OrderCreated'
        assert stats['published'] == 1
        assert stats['processed'] == 2
        assert stats['processing_time'] is not None

    def test_get_event_stats_nonexistent(self):
        """Test statistiques pour événement inexistant"""
        collector = EventMetricsCollector()
        stats = collector.get_event_stats('NonexistentEvent')
        assert stats is None

    def test_get_handler_stats(self):
        """Test statistiques pour un handler"""
        collector = EventMetricsCollector()

        collector.record_handler_execution('handle_order', 'OrderCreated', 10.0)
        collector.record_handler_execution('handle_order', 'OrderCreated', 20.0)

        stats = collector.get_handler_stats('handle_order')

        assert stats['handler'] == 'handle_order'
        assert stats['executions'] == 2
        assert stats['avg_duration_ms'] == 15.0

    def test_top_events(self):
        """Test obtenir les événements les plus fréquents"""
        collector = EventMetricsCollector()

        # Publish different events with different frequencies
        for _ in range(10):
            collector.record_event_published('OrderCreated')
        for _ in range(5):
            collector.record_event_published('PaymentProcessing')
        for _ in range(3):
            collector.record_event_published('OrderShipped')

        summary = collector.get_summary()
        top_events = summary['top_events']

        assert len(top_events) == 3
        assert top_events[0]['event_type'] == 'OrderCreated'
        assert top_events[0]['count'] == 10
        assert top_events[1]['event_type'] == 'PaymentProcessing'
        assert top_events[1]['count'] == 5

    def test_reset(self):
        """Test réinitialisation du collecteur"""
        collector = EventMetricsCollector()

        collector.record_event_published('OrderCreated')
        collector.record_event_processed('OrderCreated', 10.0)

        collector.reset()

        summary = collector.get_summary()
        assert summary['total_events'] == 0
        assert summary['total_processed'] == 0


class TestCollectMetricsDecorator:
    """Tests pour le décorateur @collect_metrics"""

    def test_decorator_on_sync_function(self):
        """Test décorateur sur fonction synchrone"""
        collector = get_metrics_collector()
        collector.reset()

        class MockEvent:
            pass

        @collect_metrics
        def handle_event(event):
            return "processed"

        event = MockEvent()
        result = handle_event(event)

        assert result == "processed"
        assert collector.events_processed.get('MockEvent') == 1

    def test_decorator_on_sync_function_with_error(self):
        """Test décorateur sur fonction avec erreur"""
        collector = get_metrics_collector()
        collector.reset()

        class MockEvent:
            pass

        @collect_metrics
        def failing_handler(event):
            raise ValueError("Test error")

        event = MockEvent()

        with pytest.raises(ValueError):
            failing_handler(event)

        # Should still record the failure
        assert collector.events_failed.get('MockEvent') == 1

    def test_decorator_on_async_function(self):
        """Test décorateur sur fonction asynchrone"""
        pytest.importorskip("pytest_asyncio")
        import asyncio

        collector = get_metrics_collector()
        collector.reset()

        class MockEvent:
            pass

        @collect_metrics
        async def async_handler(event):
            await asyncio.sleep(0.01)
            return "async processed"

        event = MockEvent()
        result = asyncio.run(async_handler(event))

        assert result == "async processed"
        assert collector.events_processed.get('MockEvent') == 1

    def test_decorator_measures_duration(self):
        """Test que le décorateur mesure la durée d'exécution"""
        collector = get_metrics_collector()
        collector.reset()

        class MockEvent:
            pass

        @collect_metrics
        def slow_handler(event):
            time.sleep(0.05)  # 50ms
            return "done"

        event = MockEvent()
        slow_handler(event)

        # Check that duration was recorded
        avg_duration = collector.handler_execution.get_average('slow_handler:MockEvent')
        assert avg_duration is not None
        assert avg_duration >= 40  # At least 40ms (accounting for timing variance)


class TestTradingScenarioMetrics:
    """Tests des métriques dans un contexte de trading"""

    def test_order_processing_metrics(self):
        """Test métriques de traitement de commandes"""
        collector = EventMetricsCollector()

        # Simuler 100 commandes
        for i in range(100):
            collector.record_event_published('OrderCreated')

            # 95% success rate
            if i < 95:
                collector.record_event_processed('OrderCreated', 10.0 + (i % 20))
            else:
                collector.record_event_failed('OrderCreated', 50.0)

        stats = collector.get_event_stats('OrderCreated')

        assert stats['published'] == 100
        assert stats['processed'] == 95
        assert stats['failed'] == 5
        assert stats['error_rate'] == 5.0

    def test_high_frequency_trading_metrics(self):
        """Test métriques pour trading haute fréquence"""
        collector = EventMetricsCollector()

        # Simuler 1000 événements de trading rapides
        for i in range(1000):
            collector.record_event_published('MarketTick')
            collector.record_event_processed('MarketTick', 0.5 + (i % 10) * 0.1)

        summary = collector.get_summary()

        assert summary['total_events'] == 1000
        assert summary['total_processed'] == 1000
        assert summary['error_rate'] == 0.0

        # Check processing time
        avg_time = collector.processing_time.get_average('MarketTick')
        assert avg_time < 2.0  # Should be fast

    def test_mixed_event_types_trading(self):
        """Test métriques avec plusieurs types d'événements de trading"""
        collector = EventMetricsCollector()

        # Different event types with different frequencies
        event_types = [
            ('MarketTick', 100, 0.5),
            ('OrderCreated', 50, 10.0),
            ('OrderFilled', 45, 15.0),
            ('OrderCancelled', 5, 5.0),
        ]

        for event_type, count, duration in event_types:
            for _ in range(count):
                collector.record_event_published(event_type)
                collector.record_event_processed(event_type, duration)

        summary = collector.get_summary()

        # Check top events
        top_events = summary['top_events']
        assert top_events[0]['event_type'] == 'MarketTick'
        assert top_events[0]['count'] == 100

        # Check individual stats
        tick_stats = collector.get_event_stats('MarketTick')
        assert tick_stats['published'] == 100
        assert tick_stats['processing_time']['avg'] == 0.5

    def test_flash_crash_volatility_metrics(self):
        """Test métriques pendant un flash crash"""
        collector = EventMetricsCollector()

        # Normal trading
        for _ in range(50):
            collector.record_event_published('MarketTick')
            collector.record_event_processed('MarketTick', 1.0)

        # Flash crash - higher latency and failures
        for i in range(50):
            collector.record_event_published('MarketTick')
            if i % 5 == 0:  # 20% failure rate during crash
                collector.record_event_failed('MarketTick', 100.0)
            else:
                collector.record_event_processed('MarketTick', 50.0)  # High latency

        stats = collector.get_event_stats('MarketTick')

        assert stats['published'] == 100
        assert stats['failed'] == 10  # 20% of 50 crash events
        # Error rate should be around 11% (10 failures out of 90 total processed+failed)
        assert 10.0 <= stats['error_rate'] <= 12.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
