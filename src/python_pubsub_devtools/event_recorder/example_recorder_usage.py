#!/usr/bin/env python3
"""
Example usage of Event Recorder and Replayer

This script demonstrates how to:
1. Record a trading bot session
2. Save the recording
3. Replay it later at different speeds
4. Analyze recorded events
"""
import sys
import time
from pathlib import Path

# Add project root to path to import from python_pubsub_risk
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from event_recorder import EventRecorder, EventReplayer
from unittest.mock import Mock
from python_pubsub_risk.events import (
    BotMonitoringCycleStarted,
    MarketPriceFetched,
    IndicatorsCalculated,
    BuyConditionMet,
    BotMonitoringCycleCompleted
)
from decimal import Decimal


def example_1_basic_recording():
    """Example 1: Basic recording of events"""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Recording")
    print("=" * 80)

    # Create a mock service bus
    service_bus = Mock()
    service_bus.publish = Mock()

    # Create and start recorder
    recorder = EventRecorder("example_basic_session")
    recorder.start_recording(service_bus)

    # Simulate some trading events
    print("\n📊 Simulating trading events...")

    # Cycle started
    service_bus.publish(
        "BotMonitoringCycleStarted",
        BotMonitoringCycleStarted(
            cycle_number=1,
            timestamp="2025-10-12T10:00:00+00:00"
        ),
        "Orchestrator"
    )
    time.sleep(0.5)

    # Market price fetched
    service_bus.publish(
        "MarketPriceFetched",
        MarketPriceFetched(
            cycle_id=1,
            current_price=Decimal("50000.0"),
            current_buy_price=Decimal("50010.0"),
            current_sell_price=Decimal("49990.0"),
            timestamp="2025-10-12T10:00:01+00:00",
            pair="BTC/USDT",
            candles=[]
        ),
        "MarketPriceFetcher"
    )
    time.sleep(0.3)

    # Indicators calculated
    service_bus.publish(
        "IndicatorsCalculated",
        IndicatorsCalculated(
            cycle_id=1,
            indicators=[
                {"name": "RSI", "value": 65.0, "buy_signal": True, "sell_signal": False},
                {"name": "MACD", "value": 120.0, "buy_signal": True, "sell_signal": False}
            ],
            timestamp="2025-10-12T10:00:02+00:00",
            candles_count=100,
            current_price=Decimal("50000.0")
        ),
        "IndicatorCalculation"
    )
    time.sleep(0.2)

    # Buy condition met
    service_bus.publish(
        "BuyConditionMet",
        BuyConditionMet(
            cycle_id=1,
            indicators=[
                {"name": "RSI", "value": 65.0, "buy_signal": True, "sell_signal": False},
                {"name": "MACD", "value": 120.0, "buy_signal": True, "sell_signal": False}
            ],
            timestamp="2025-10-12T10:00:03+00:00",
            current_price=Decimal("50000.0")
        ),
        "BuyConditionEvaluator"
    )
    time.sleep(0.4)

    # Cycle completed
    service_bus.publish(
        "BotMonitoringCycleCompleted",
        BotMonitoringCycleCompleted(
            cycle_number=1,
            duration_ms=3000,
            timestamp="2025-10-12T10:00:03+00:00"
        ),
        "CycleCompletionDetector"
    )

    # Stop and save
    recorder.stop_recording()
    filepath = recorder.save()

    print(f"\n✅ Recording saved to: {filepath}")
    return str(filepath)


def example_2_replay_recording(recording_file: str):
    """Example 2: Replay a recorded session"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Replaying Recording")
    print("=" * 80)

    # Create replayer
    replayer = EventReplayer(recording_file)

    # Show event summary
    print("\n📊 Event Summary:")
    for event_name, count in replayer.get_event_summary().items():
        print(f"  {event_name:50s} {count:3d}x")

    # Show timeline
    replayer.print_timeline()

    # Replay at different speeds
    print("\n🎬 Replaying at 1x speed...")
    service_bus = Mock()
    service_bus.publish = Mock()

    # Track published events
    published_events = []

    def event_tracker(event_name, event, source):
        published_events.append(event_name)
        print(f"  ✓ Replayed: {event_name}")

    # Temporarily replace publish to track
    original_publish = service_bus.publish
    service_bus.publish = lambda name, event, src: (event_tracker(name, event, src), original_publish(name, event, src))[1]

    replayer.replay(service_bus, speed_multiplier=1.0)

    print(f"\n✅ Replayed {len(published_events)} events")


def example_3_replay_with_filter(recording_file: str):
    """Example 3: Replay only specific events"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Filtered Replay (Only 'Met' and 'Fetched' events)")
    print("=" * 80)

    replayer = EventReplayer(recording_file)
    service_bus = Mock()
    service_bus.publish = Mock()

    published_events = []

    def event_tracker(event_name, event, source):
        published_events.append(event_name)
        print(f"  ✓ Replayed: {event_name}")

    original_publish = service_bus.publish
    service_bus.publish = lambda name, event, src: (event_tracker(name, event, src), original_publish(name, event, src))[1]

    # Replay only events with "Met" or "Fetched" in name
    replayer.replay(
        service_bus,
        speed_multiplier=10.0,
        event_filter=lambda name: "Met" in name or "Fetched" in name
    )

    print(f"\n✅ Replayed {len(published_events)} filtered events")


def example_4_context_manager():
    """Example 4: Using recorder as context manager"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Context Manager Usage")
    print("=" * 80)

    service_bus = Mock()
    service_bus.publish = Mock()

    with EventRecorder("context_example") as recorder:
        recorder.start_recording(service_bus)

        print("\n📊 Publishing events within context...")

        for i in range(3):
            service_bus.publish(
                "BotMonitoringCycleStarted",
                BotMonitoringCycleStarted(
                    cycle_number=i + 1,
                    timestamp=f"2025-10-12T10:00:{i:02d}+00:00"
                ),
                "Orchestrator"
            )
            time.sleep(0.1)

        filepath = recorder.save("context_recording")

    print(f"\n✅ Recording saved: {filepath}")
    print("✅ Context manager automatically stopped recording")


def example_5_speed_comparison(recording_file: str):
    """Example 5: Compare replay speeds"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Speed Comparison")
    print("=" * 80)

    replayer = EventReplayer(recording_file)

    speeds = [1.0, 5.0, 10.0, 50.0]

    for speed in speeds:
        service_bus = Mock()
        service_bus.publish = Mock()

        print(f"\n⏱️  Testing {speed}x speed...")
        start = time.time()
        replayer.replay(service_bus, speed_multiplier=speed)
        duration = time.time() - start

        print(f"  Duration: {duration:.3f}s")


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("EVENT RECORDER/REPLAYER EXAMPLES")
    print("=" * 80)

    # Example 1: Record events
    recording_file = example_1_basic_recording()

    # Example 2: Replay recording
    example_2_replay_recording(recording_file)

    # Example 3: Filtered replay
    example_3_replay_with_filter(recording_file)

    # Example 4: Context manager
    example_4_context_manager()

    # Example 5: Speed comparison
    example_5_speed_comparison(recording_file)

    print("\n" + "=" * 80)
    print("✅ All examples completed!")
    print("=" * 80)

    print("\n💡 Tips:")
    print("  - Use recordings to reproduce bugs exactly as they occurred")
    print("  - Replay at high speed (10x-100x) for faster testing")
    print("  - Filter events to focus on specific behaviors")
    print("  - Use context manager for automatic cleanup")
    print("  - Recordings are stored in tools/recordings/")


if __name__ == '__main__':
    main()
