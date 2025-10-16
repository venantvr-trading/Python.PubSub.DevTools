#!/usr/bin/env python3
"""
Example: Using Event Flow Scanner

Demonstrates how to use the EventFlowScanner to push graph data to the API.
"""
from pathlib import Path
from python_pubsub_devtools.event_flow import EventFlowScanner


def example_one_shot_scan():
    """Example: Run scanner once and exit"""
    print("=" * 60)
    print("Example 1: One-shot scan")
    print("=" * 60)
    print()

    # Configure paths
    agents_dir = Path("../python_pubsub_risk/agents")
    events_dir = Path("../python_pubsub_risk/events")
    api_url = "http://localhost:5555"

    # Create scanner
    scanner = EventFlowScanner(
        agents_dir=agents_dir,
        events_dir=events_dir,
        api_url=api_url
    )

    # Run once
    results = scanner.scan_once()

    # Check results
    print()
    print("Results:")
    for graph_type, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"  {graph_type}: {status}")


def example_continuous_scan():
    """Example: Run scanner continuously"""
    print("=" * 60)
    print("Example 2: Continuous scan (every 60 seconds)")
    print("=" * 60)
    print()

    # Configure paths
    agents_dir = Path("../python_pubsub_risk/agents")
    events_dir = Path("../python_pubsub_risk/events")
    api_url = "http://localhost:5555"

    # Create scanner with interval
    scanner = EventFlowScanner(
        agents_dir=agents_dir,
        events_dir=events_dir,
        api_url=api_url,
        interval=60  # Scan every 60 seconds
    )

    # Run continuously (press Ctrl+C to stop)
    scanner.run_continuous()


def example_programmatic_api_query():
    """Example: Query API programmatically"""
    import requests

    print("=" * 60)
    print("Example 3: Query API programmatically")
    print("=" * 60)
    print()

    api_url = "http://localhost:5555"

    # Get cache status
    response = requests.get(f"{api_url}/api/graph/status")
    if response.status_code == 200:
        status = response.json()
        print("Cache status:")
        print(f"  Total graphs: {status['total_graphs']}")
        print(f"  Graphs:")
        for graph_type, info in status['graphs'].items():
            print(f"    - {graph_type}: {info['timestamp']}")
    else:
        print(f"Failed to get status: {response.status_code}")

    print()

    # Get DOT content for a specific graph
    graph_type = "complete"
    response = requests.get(f"{api_url}/api/graph/{graph_type}?format=dot")
    if response.status_code == 200:
        dot_content = response.text
        print(f"DOT content for '{graph_type}' graph:")
        print(dot_content[:200] + "...")  # Print first 200 chars
    else:
        print(f"Failed to get graph: {response.status_code}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1]

        if mode == "one-shot":
            example_one_shot_scan()
        elif mode == "continuous":
            example_continuous_scan()
        elif mode == "api-query":
            example_programmatic_api_query()
        else:
            print(f"Unknown mode: {mode}")
            print("Usage: python scanner_usage.py [one-shot|continuous|api-query]")
            sys.exit(1)
    else:
        print("Event Flow Scanner Examples")
        print()
        print("Usage:")
        print("  python scanner_usage.py one-shot      - Run scanner once and exit")
        print("  python scanner_usage.py continuous    - Run scanner continuously")
        print("  python scanner_usage.py api-query     - Query API programmatically")
        print()
        print("Make sure the event_flow API is running before using the scanner:")
        print("  pubsub-tools event-flow --config devtools_config.yaml")
