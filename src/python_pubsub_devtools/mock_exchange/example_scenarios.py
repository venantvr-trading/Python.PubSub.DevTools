#!/usr/bin/env python3
"""
Example usage of Scenario-Based Mock Exchange

Demonstrates all available market scenarios and their characteristics.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scenario_exchange import ScenarioBasedMockExchange, MarketScenario


def print_header(title: str):
    """Print formatted section header"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def run_scenario(scenario: MarketScenario, calls: int = 50, initial_price: float = 50000.0):
    """Run a scenario and display results"""
    print(f"🎯 Scenario: {scenario.value.upper().replace('_', ' ')}")
    print(f"   Initial Price: ${initial_price:,.2f}")
    print(f"   Simulating {calls} candles...")

    exchange = ScenarioBasedMockExchange(
        scenario=scenario,
        initial_price=initial_price
    )

    # Fetch prices
    for _ in range(calls):
        exchange.fetch_current_price()

    # Get statistics
    stats = exchange.get_price_statistics()

    # Display results
    print(f"\n   Results:")
    print(f"     Final Price:    ${exchange.current_price:,.2f}")
    print(f"     Min Price:      ${stats['min_price']:,.2f}")
    print(f"     Max Price:      ${stats['max_price']:,.2f}")
    print(f"     Total Return:   {stats['total_return_pct']:+.2f}%")
    print(f"     Volatility:     {stats['volatility']:.4f}")
    print()


def example_1_all_scenarios():
    """Example 1: Run all scenarios and compare"""
    print_header("Example 1: All Market Scenarios")

    scenarios = [
        MarketScenario.BULL_RUN,
        MarketScenario.BEAR_CRASH,
        MarketScenario.SIDEWAYS,
        MarketScenario.FLASH_CRASH,
        MarketScenario.VOLATILE,
        MarketScenario.PUMP_AND_DUMP,
        MarketScenario.DEAD_CAT_BOUNCE,
        MarketScenario.ACCUMULATION,
        MarketScenario.DISTRIBUTION,
    ]

    for scenario in scenarios:
        run_scenario(scenario, calls=50)


def example_2_bull_run_detailed():
    """Example 2: Detailed bull run analysis"""
    print_header("Example 2: Bull Run Detailed Analysis")

    exchange = ScenarioBasedMockExchange(
        scenario=MarketScenario.BULL_RUN,
        initial_price=50000.0
    )

    print("📈 Tracking price evolution every 10 candles:\n")

    for i in range(1, 101):
        price_data = exchange.fetch_current_price()

        if i % 10 == 0:
            stats = exchange.get_price_statistics()
            print(f"   Candle {i:3d}: ${price_data.current_price.price:,.2f}  "
                  f"(Return: {stats['total_return_pct']:+.2f}%)")

    final_stats = exchange.get_price_statistics()
    print(f"\n   ✅ Final Return: {final_stats['total_return_pct']:+.2f}%")


def example_3_flash_crash_phases():
    """Example 3: Flash crash with different phases"""
    print_header("Example 3: Flash Crash Phase Analysis")

    exchange = ScenarioBasedMockExchange(
        scenario=MarketScenario.FLASH_CRASH,
        initial_price=50000.0
    )

    print("⚡ Flash Crash Phases:\n")

    phases = [
        (15, "Pre-crash (normal)"),
        (25, "During crash"),
        (40, "Recovery"),
        (55, "Post-recovery")
    ]

    for target_call, phase_name in phases:
        while exchange.call_count < target_call:
            price_data = exchange.fetch_current_price()

        stats = exchange.get_price_statistics()
        print(f"   {phase_name:20s} (candle {target_call}): "
              f"${exchange.current_price:,.2f}  "
              f"({stats['total_return_pct']:+.2f}%)")


def example_4_volatility_comparison():
    """Example 4: Compare volatility across scenarios"""
    print_header("Example 4: Volatility Comparison")

    scenarios = [
        MarketScenario.SIDEWAYS,
        MarketScenario.BULL_RUN,
        MarketScenario.VOLATILE,
    ]

    print("📊 Volatility Ranking:\n")

    results = []
    for scenario in scenarios:
        exchange = ScenarioBasedMockExchange(
            scenario=scenario,
            initial_price=50000.0
        )

        for _ in range(100):
            exchange.fetch_current_price()

        stats = exchange.get_price_statistics()
        results.append((scenario.value, stats['volatility']))

    # Sort by volatility
    results.sort(key=lambda x: x[1])

    for i, (name, vol) in enumerate(results, 1):
        bars = "█" * int(vol * 1000)
        print(f"   {i}. {name:20s}: {vol:.4f}  {bars}")


def example_5_custom_parameters():
    """Example 5: Custom parameters"""
    print_header("Example 5: Custom Parameters")

    print("🎛️  Testing custom volatility multiplier:\n")

    multipliers = [0.5, 1.0, 2.0]

    for mult in multipliers:
        exchange = ScenarioBasedMockExchange(
            scenario=MarketScenario.VOLATILE,
            initial_price=50000.0,
            volatility_multiplier=mult
        )

        for _ in range(50):
            exchange.fetch_current_price()

        stats = exchange.get_price_statistics()
        print(f"   Multiplier {mult:3.1f}x:  "
              f"Volatility={stats['volatility']:.4f}  "
              f"Range=${stats['max_price'] - stats['min_price']:,.2f}")


def example_6_spread_testing():
    """Example 6: Bid-ask spread testing"""
    print_header("Example 6: Bid-Ask Spread Testing")

    spreads = [10, 20, 50, 100]  # basis points

    print("💱 Testing different spreads:\n")

    for spread_bps in spreads:
        exchange = ScenarioBasedMockExchange(
            scenario=MarketScenario.SIDEWAYS,
            initial_price=50000.0,
            spread_bps=spread_bps
        )

        price_data = exchange.fetch_current_price()

        current = price_data.current_price.price
        buy = price_data.buy_price.price
        sell = price_data.sell_price.price

        actual_spread = ((buy - sell) / current) * 10000

        print(f"   Spread {spread_bps:3d} bps:  "
              f"Buy=${buy:,.2f}  "
              f"Sell=${sell:,.2f}  "
              f"(Actual: {actual_spread:.1f} bps)")


def example_7_irregular_candles():
    """Example 7: Detecting irregular candles"""
    print_header("Example 7: Irregular Candles Detection")

    exchange = ScenarioBasedMockExchange(
        scenario=MarketScenario.IRREGULAR_CANDLES,
        initial_price=50000.0
    )

    print("🔍 Checking for irregular timestamp intervals:\n")

    for _ in range(30):
        exchange.fetch_current_price()

    candles = exchange._historical_candles
    intervals = candles['timestamp'].diff().dropna()
    unique_intervals = sorted(intervals.unique())

    print(f"   Total candles:        {len(candles)}")
    print(f"   Unique intervals:     {len(unique_intervals)}")
    print(f"   Interval values (ms): {[int(i) for i in unique_intervals]}")

    if len(unique_intervals) > 1:
        print(f"\n   ⚠️  Irregular intervals detected! This will trigger candle validation errors.")
    else:
        print(f"\n   ✅ All intervals regular.")


def example_8_pump_and_dump_timing():
    """Example 8: Pump and dump timing"""
    print_header("Example 8: Pump and Dump Timing")

    exchange = ScenarioBasedMockExchange(
        scenario=MarketScenario.PUMP_AND_DUMP,
        initial_price=50000.0
    )

    print("🚀💥 Tracking pump and dump phases:\n")

    checkpoints = [5, 10, 15, 20, 25, 30, 35, 40]

    for checkpoint in checkpoints:
        while exchange.call_count < checkpoint:
            exchange.fetch_current_price()

        stats = exchange.get_price_statistics()

        phase = ""
        if checkpoint <= 20:
            phase = "🚀 PUMP"
        elif checkpoint <= 35:
            phase = "💥 DUMP"
        else:
            phase = "📊 STABLE"

        print(f"   Candle {checkpoint:2d} {phase:12s}: "
              f"${exchange.current_price:,.2f}  "
              f"({stats['total_return_pct']:+.2f}%)")


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("  SCENARIO-BASED MOCK EXCHANGE - EXAMPLES")
    print("=" * 80)

    example_1_all_scenarios()
    example_2_bull_run_detailed()
    example_3_flash_crash_phases()
    example_4_volatility_comparison()
    example_5_custom_parameters()
    example_6_spread_testing()
    example_7_irregular_candles()
    example_8_pump_and_dump_timing()

    print("\n" + "=" * 80)
    print("  ✅ ALL EXAMPLES COMPLETED")
    print("=" * 80)

    print("\n💡 Tips:")
    print("  - Use scenarios in parametrized tests: @pytest.mark.parametrize")
    print("  - Test edge cases: flash crashes, irregular candles")
    print("  - Combine with EventRecorder to capture scenario behavior")
    print("  - Adjust volatility_multiplier for stress testing")
    print("  - Use reset() to rerun same scenario multiple times\n")


if __name__ == '__main__':
    main()
