#!/usr/bin/env python3
"""
Example usage of Scenario Testing Framework

Demonstrates how to use the framework both via CLI and programmatically.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scenario_runner import ScenarioRunner


def example_1_run_single_scenario():
    """Example 1: Run a single scenario"""
    print("\n" + "=" * 80)
    print("  Example 1: Run Single Scenario")
    print("=" * 80 + "\n")

    scenario_path = Path(__file__).parent / "scenarios" / "flash_crash_recovery.yaml"

    runner = ScenarioRunner(str(scenario_path))
    results = runner.run()

    print(f"\n✅ Scenario: {results['scenario']['name']}")
    print(f"   Status: {results['status']}")
    print(f"   Duration: {results['duration_seconds']:.2f}s")
    print(f"   Assertions: {results['assertions']['passed']}/{results['assertions']['total']} passed")

    if results.get('chaos'):
        print(f"\n🔥 Chaos Statistics:")
        for key, value in results['chaos'].items():
            print(f"   {key}: {value}")


def example_2_run_all_scenarios():
    """Example 2: Run all scenarios in directory"""
    print("\n" + "=" * 80)
    print("  Example 2: Run All Scenarios")
    print("=" * 80 + "\n")

    scenarios_dir = Path(__file__).parent / "scenarios"
    scenario_files = list(scenarios_dir.glob("*.yaml"))

    print(f"Found {len(scenario_files)} scenarios\n")

    results_summary = []

    for scenario_file in scenario_files:
        print(f"Running: {scenario_file.name}...")

        runner = ScenarioRunner(str(scenario_file))
        results = runner.run()

        results_summary.append({
            "name": results['scenario']['name'],
            "status": results['status'],
            "assertions_passed": results['assertions']['passed'],
            "assertions_total": results['assertions']['total']
        })

        print(f"  {'✅' if results['status'] == 'passed' else '❌'} {results['status'].upper()}\n")

    # Print summary
    print("\n" + "=" * 80)
    print("  SUMMARY")
    print("=" * 80)

    passed = sum(1 for r in results_summary if r['status'] == 'passed')
    total = len(results_summary)

    print(f"\n  Overall: {passed}/{total} scenarios passed\n")

    for result in results_summary:
        status_icon = "✅" if result['status'] == 'passed' else "❌"
        print(f"  {status_icon} {result['name']:<50s} {result['assertions_passed']}/{result['assertions_total']} assertions")

    print("\n" + "=" * 80 + "\n")


def example_3_create_scenario_programmatically():
    """Example 3: Create and run scenario programmatically (without YAML)"""
    print("\n" + "=" * 80)
    print("  Example 3: Programmatic Scenario Creation")
    print("=" * 80 + "\n")

    from scenario_schema import (
        TestScenario, Setup, ExchangeSetup, BotSetup,
        DelayEventChaos, InjectFailureChaos
    )

    # Create scenario object
    scenario = TestScenario(
        name="Programmatic Test",
        description="A scenario created via Python code",
        setup=Setup(
            exchange=ExchangeSetup(
                scenario="sideways",
                initial_price=50000.0
            ),
            bot=BotSetup(
                initial_capital=10000.0,
                pool_count=5
            )
        ),
        chaos=[
            DelayEventChaos(
                event="IndicatorsCalculated",
                delay_ms=2000,
                at_cycle=10
            ),
            InjectFailureChaos(
                event="MarketPriceFetchFailed",
                at_cycle=20,
                error_message="Programmatic failure injection"
            )
        ],
        steps=[
            {"wait_for_cycles": 30},
            {
                "assert": {
                    "event_count": {
                        "BotMonitoringCycleStarted": {"min": 30}
                    }
                }
            }
        ]
    )

    # Save to temporary YAML
    import yaml

    temp_scenario_path = Path("/tmp/programmatic_scenario.yaml")

    with open(temp_scenario_path, 'w') as f:
        yaml.dump(scenario.model_dump(by_alias=True), f, default_flow_style=False)

    print(f"📝 Created scenario at {temp_scenario_path}")

    # Run it
    runner = ScenarioRunner(str(temp_scenario_path))
    results = runner.run()

    print(f"\n✅ Status: {results['status']}")
    print(f"   Assertions: {results['assertions']['passed']}/{results['assertions']['total']} passed")


def example_4_custom_assertions():
    """Example 4: Using custom assertion functions"""
    print("\n" + "=" * 80)
    print("  Example 4: Custom Assertions")
    print("=" * 80 + "\n")

    from assertion_checker import AssertionChecker

    # Mock some events
    events = [
        {"event_name": "BotMonitoringCycleStarted", "cycle": 1},
        {"event_name": "MarketPriceFetched", "cycle": 1},
        {"event_name": "IndicatorsCalculated", "cycle": 1},
        {"event_name": "BuyConditionMet", "cycle": 1},
        {"event_name": "PositionPurchased", "cycle": 1, "event_data": {"purchase_price": 50000}},
        {"event_name": "BotMonitoringCycleStarted", "cycle": 2},
        {"event_name": "PositionSold", "cycle": 2, "event_data": {"sale_price": 52000}},
    ]

    # Custom assertion function
    def assert_profitable_trade(events):
        """Check that we made a profitable trade"""
        purchases = [e for e in events if e['event_name'] == 'PositionPurchased']
        sales = [e for e in events if e['event_name'] == 'PositionSold']

        if not purchases or not sales:
            return False, "No trades found"

        purchase_price = purchases[0]['event_data']['purchase_price']
        sale_price = sales[0]['event_data']['sale_price']

        if sale_price > purchase_price:
            profit_pct = ((sale_price - purchase_price) / purchase_price) * 100
            return True, f"Profitable trade: {profit_pct:.2f}% profit"
        else:
            return False, f"Unprofitable trade"

    # Run assertions
    checker = AssertionChecker(events)
    checker._check_custom_assertion(assert_profitable_trade)

    for result in checker.results:
        print(f"  {result}")


def example_5_cli_usage():
    """Example 5: CLI usage examples"""
    print("\n" + "=" * 80)
    print("  Example 5: CLI Usage Examples")
    print("=" * 80 + "\n")

    print("CLI Commands:\n")

    print("1. Run a single scenario:")
    print("   python scenario_runner.py scenarios/flash_crash_recovery.yaml\n")

    print("2. Run with JSON output:")
    print("   python scenario_runner.py scenarios/bull_run_profit.yaml --output results.json\n")

    print("3. Run with verbose logging:")
    print("   python scenario_runner.py scenarios/chaos_resilience.yaml --verbose\n")

    print("4. Run all scenarios with bash:")
    print("   for f in scenarios/*.yaml; do python scenario_runner.py \"$f\"; done\n")


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("  SCENARIO TESTING FRAMEWORK - EXAMPLES")
    print("=" * 80)

    example_1_run_single_scenario()
    # example_2_run_all_scenarios()  # Commented out to save time
    example_3_create_scenario_programmatically()
    example_4_custom_assertions()
    example_5_cli_usage()

    print("\n" + "=" * 80)
    print("  ✅ ALL EXAMPLES COMPLETED")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
