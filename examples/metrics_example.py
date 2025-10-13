#!/usr/bin/env python
"""
Example: Using Event Metrics Collector

This example demonstrates how to use the metrics collector to monitor events.
"""
import time
import random
from python_pubsub_devtools.metrics import get_metrics_collector, collect_metrics


class OrderCreatedEvent:
    """Mock order created event"""
    def __init__(self, order_id):
        self.order_id = order_id


class PaymentProcessingEvent:
    """Mock payment processing event"""
    def __init__(self, payment_id):
        self.payment_id = payment_id


@collect_metrics
def handle_order_created(event):
    """Handle order creation with automatic metrics collection"""
    # Simulate processing
    time.sleep(random.uniform(0.01, 0.03))

    # Simulate occasional failures
    if random.random() < 0.05:  # 5% failure rate
        raise Exception("Order validation failed")

    return f"Order {event.order_id} processed"


@collect_metrics
def handle_payment_processing(event):
    """Handle payment with automatic metrics collection"""
    # Simulate payment processing
    time.sleep(random.uniform(0.02, 0.05))

    # Simulate occasional failures
    if random.random() < 0.10:  # 10% failure rate
        raise Exception("Payment declined")

    return f"Payment {event.payment_id} processed"


def main():
    """Run the metrics example"""
    print("=" * 80)
    print("Event Metrics Collector Example")
    print("=" * 80)
    print()

    collector = get_metrics_collector()
    collector.reset()  # Start fresh

    print("Processing 100 orders and payments...")
    print()

    # Process events
    for i in range(100):
        # Order events
        collector.record_event_published('OrderCreatedEvent')
        try:
            event = OrderCreatedEvent(order_id=f"ORD-{i:04d}")
            handle_order_created(event)
        except Exception:
            pass  # Handler already records the failure

        # Payment events
        collector.record_event_published('PaymentProcessingEvent')
        try:
            event = PaymentProcessingEvent(payment_id=f"PAY-{i:04d}")
            handle_payment_processing(event)
        except Exception:
            pass  # Handler already records the failure

    print("✅ Processing complete!")
    print()

    # Display summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    summary = collector.get_summary()

    print(f"Total Events Published:  {summary['total_events']:,}")
    print(f"Total Events Processed:  {summary['total_processed']:,}")
    print(f"Total Events Failed:     {summary['total_failed']:,}")
    print(f"Error Rate:              {summary['error_rate']:.2f}%")
    print(f"Avg Processing Time:     {summary['avg_processing_time_ms']:.2f} ms")
    print()

    # Top events
    print("Top Events:")
    for event in summary['top_events'][:5]:
        percentage = (event['count'] / summary['total_events'] * 100) if summary['total_events'] > 0 else 0
        print(f"  {event['event_type']:30s} {event['count']:4d} ({percentage:5.1f}%)")
    print()

    # Handler stats
    print("=" * 80)
    print("HANDLER STATISTICS")
    print("=" * 80)

    for handler in ['handle_order_created', 'handle_payment_processing']:
        stats = collector.get_handler_stats(handler)
        if stats['executions'] > 0:
            print(f"\n{handler}:")
            print(f"  Executions:    {stats['executions']:,}")
            print(f"  Avg Duration:  {stats['avg_duration_ms']:.2f} ms")
            print(f"  Min Duration:  {stats['min_duration_ms']:.2f} ms")
            print(f"  Max Duration:  {stats['max_duration_ms']:.2f} ms")

    print()

    # Event-specific stats
    print("=" * 80)
    print("EVENT-SPECIFIC STATISTICS")
    print("=" * 80)

    for event_type in ['OrderCreatedEvent', 'PaymentProcessingEvent']:
        stats = collector.get_event_stats(event_type)
        if stats:
            print(f"\n{event_type}:")
            print(f"  Published:   {stats['published']:,}")
            print(f"  Processed:   {stats['processed']:,}")
            print(f"  Failed:      {stats['failed']:,}")
            print(f"  Error Rate:  {stats['error_rate']:.2f}%")

            if stats['processing_time']:
                pt = stats['processing_time']
                print(f"  Processing Time:")
                print(f"    Avg:  {pt['avg']:.2f} ms")
                print(f"    P50:  {pt['p50']:.2f} ms")
                print(f"    P95:  {pt['p95']:.2f} ms")
                print(f"    P99:  {pt['p99']:.2f} ms")

    print()
    print("=" * 80)
    print("Use 'pubsub-tools metrics show' to view metrics via CLI")
    print("=" * 80)


if __name__ == '__main__':
    main()
