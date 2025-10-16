"""
Event Flow Scanner - Autonomous service to scan codebase and push graphs to API

Scans agent code periodically, generates graph data, and POSTs to the event_flow API.
Can run in one-shot mode or continuous mode with configurable interval.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Set

import requests

from .analyze_event_flow import EventFlowAnalyzer


class EventFlowScanner:
    """
    Scanner service that analyzes event flow and pushes to API

    Attributes:
        agents_dir: Directory containing agent code
        events_dir: Directory containing event definitions
        api_url: Base URL of the event_flow API
        interval: Scan interval in seconds (None for one-shot)
    """

    def __init__(
        self,
        agents_dir: Path,
        events_dir: Optional[Path] = None,
        api_url: str = "http://localhost:5555",
        interval: Optional[int] = None,
    ):
        """
        Initialize scanner

        Args:
            agents_dir: Path to agents directory
            events_dir: Path to events directory (optional, for namespace info)
            api_url: Base URL of event_flow API
            interval: Scan interval in seconds (None for one-shot mode)
        """
        self.agents_dir = agents_dir
        self.events_dir = events_dir
        self.api_url = api_url.rstrip('/')
        self.interval = interval

        # Validate paths
        if not self.agents_dir.exists():
            raise ValueError(f"Agents directory not found: {self.agents_dir}")

    def scan_once(self) -> Dict[str, bool]:
        """
        Perform a single scan and push to API

        Returns:
            Dictionary mapping graph_type to success status
        """
        print(f"[SCAN] Starting scan at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[SCAN] Agents directory: {self.agents_dir}")

        # Analyze event flow
        analyzer = EventFlowAnalyzer(self.agents_dir)
        analyzer.analyze()

        events = analyzer.get_all_events()
        agents = set(analyzer.subscriptions.keys()) | set(analyzer.publications.keys())

        print(f"[SCAN] Found {len(events)} events, {len(agents)} agents")

        # Collect namespaces if events_dir available
        namespaces = self._get_namespaces() if self.events_dir else None

        # Generate and push each graph type
        graph_types = ['simplified', 'complete', 'full-tree']
        results = {}

        for graph_type in graph_types:
            try:
                print(f"[SCAN] Generating {graph_type} graph...")
                dot_content = self._generate_dot(analyzer, graph_type)

                if dot_content:
                    # Calculate connections (subscriptions + publications)
                    total_connections = 0
                    for event, subscribers in analyzer.event_to_subscribers.items():
                        total_connections += len(subscribers)
                    for agent, publications in analyzer.publications.items():
                        total_connections += len(publications)

                    # Prepare payload
                    payload = {
                        'graph_type': graph_type,
                        'dot_content': dot_content,
                        'stats': {
                            'events': len(events),
                            'agents': len(agents),
                            'connections': total_connections,
                        }
                    }

                    if namespaces:
                        payload['namespaces'] = list(namespaces)

                    # POST to API
                    success = self._push_to_api(payload)
                    results[graph_type] = success
                else:
                    print(f"[SCAN] Failed to generate {graph_type}")
                    results[graph_type] = False

            except Exception as e:
                print(f"[SCAN] Error processing {graph_type}: {e}")
                results[graph_type] = False

        return results

    def run_continuous(self) -> None:
        """
        Run scanner in continuous mode with configured interval

        Raises:
            ValueError: If interval is None
        """
        if self.interval is None:
            raise ValueError("Cannot run continuous mode without interval")

        print(f"[SCAN] Starting continuous scanner (interval: {self.interval}s)")
        print(f"[SCAN] API URL: {self.api_url}")
        print(f"[SCAN] Press Ctrl+C to stop")
        print()

        try:
            while True:
                results = self.scan_once()

                # Print summary
                success_count = sum(1 for s in results.values() if s)
                total_count = len(results)
                print(f"[SCAN] Completed: {success_count}/{total_count} graphs pushed successfully")
                print()

                # Wait for next cycle
                print(f"[SCAN] Sleeping for {self.interval} seconds...")
                time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\n[SCAN] Stopped by user")

    def _generate_dot(self, analyzer: EventFlowAnalyzer, graph_type: str) -> Optional[str]:
        """
        Generate DOT content for specified graph type

        Args:
            analyzer: EventFlowAnalyzer instance with analysis results
            graph_type: Type of graph (simplified, complete, full-tree)

        Returns:
            DOT content as string, or None if generation fails
        """
        temp_dir = Path(tempfile.gettempdir())
        dot_file = temp_dir / f"scan_{graph_type}.dot"

        try:
            if graph_type == 'simplified':
                from .generate_hierarchical_tree import generate_simplified_tree
                generate_simplified_tree(analyzer, str(dot_file), format='dot')

            elif graph_type == 'complete':
                # Generate complete graph (simplified version without namespace colors)
                dot_content = self._generate_complete_dot(analyzer)
                dot_file.write_text(dot_content)

            elif graph_type == 'full-tree':
                from .generate_hierarchical_tree import generate_hierarchical_tree
                generate_hierarchical_tree(analyzer, str(dot_file), format='dot')

            else:
                print(f"[SCAN] Unknown graph type: {graph_type}")
                return None

            # Read generated DOT
            if dot_file.exists():
                dot_content = dot_file.read_text()
                return dot_content
            else:
                print(f"[SCAN] DOT file not created: {dot_file}")
                return None

        except Exception as e:
            print(f"[SCAN] Error generating DOT for {graph_type}: {e}")
            return None

        finally:
            # Cleanup
            if dot_file.exists():
                dot_file.unlink()

    def _generate_complete_dot(self, analyzer: EventFlowAnalyzer) -> str:
        """
        Generate DOT content for complete graph

        Args:
            analyzer: EventFlowAnalyzer with analysis results

        Returns:
            DOT content as string
        """
        lines = ['digraph EventFlow {']
        lines.append('    rankdir=TB;')
        lines.append('    node [shape=box, style="filled,rounded", fontname="Arial", fontsize=10];')
        lines.append('    edge [arrowsize=0.8];')
        lines.append('')

        events = analyzer.get_all_events()
        agents = set(analyzer.subscriptions.keys()) | set(analyzer.publications.keys())

        # Add event nodes
        for event in sorted(events):
            lines.append(f'    "{event}" [fillcolor="#e0e0e0", shape=ellipse];')

        # Add agent nodes
        for agent in sorted(agents):
            lines.append(f'    "{agent}" [fillcolor="#ffcc80"];')

        lines.append('')

        # Add edges
        for event, subscribers in sorted(analyzer.event_to_subscribers.items()):
            for subscriber in subscribers:
                lines.append(f'    "{event}" -> "{subscriber}";')

        for agent, publications in sorted(analyzer.publications.items()):
            for event in publications:
                lines.append(f'    "{agent}" -> "{event}";')

        lines.append('}')
        return '\n'.join(lines)

    def _get_namespaces(self) -> Set[str]:
        """
        Get all event namespaces by scanning events directory

        Returns:
            Set of namespace names
        """
        if not self.events_dir or not self.events_dir.exists():
            return set()

        namespaces = set()
        for namespace_dir in self.events_dir.iterdir():
            if namespace_dir.is_dir() and not namespace_dir.name.startswith('__'):
                namespaces.add(namespace_dir.name)

        return namespaces

    def _push_to_api(self, payload: Dict) -> bool:
        """
        POST graph data to API

        Args:
            payload: Dictionary with graph data

        Returns:
            True if successful, False otherwise
        """
        endpoint = f"{self.api_url}/api/graph"

        try:
            response = requests.post(
                endpoint,
                json=payload,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 201:
                result = response.json()
                print(f"[SCAN] ✅ Pushed {payload['graph_type']} successfully")
                print(f"[SCAN]    Timestamp: {result.get('timestamp')}")
                return True
            else:
                print(f"[SCAN] ❌ Failed to push {payload['graph_type']}: {response.status_code}")
                print(f"[SCAN]    Response: {response.text}")
                return False

        except requests.exceptions.ConnectionError:
            print(f"[SCAN] ❌ Connection error - is API running at {self.api_url}?")
            return False
        except requests.exceptions.Timeout:
            print(f"[SCAN] ❌ Request timeout")
            return False
        except Exception as e:
            print(f"[SCAN] ❌ Unexpected error pushing to API: {e}")
            return False


def main():
    """CLI entry point for scanner"""
    parser = argparse.ArgumentParser(
        description="Event Flow Scanner - Scan codebase and push graphs to API"
    )
    parser.add_argument(
        '--agents-dir',
        type=str,
        required=True,
        help='Path to agents directory (required)'
    )
    parser.add_argument(
        '--events-dir',
        type=str,
        help='Path to events directory (optional, for namespace info)'
    )
    parser.add_argument(
        '--api-url',
        type=str,
        default='http://localhost:5555',
        help='Base URL of event_flow API (default: http://localhost:5555)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        help='Scan interval in seconds (omit for one-shot mode)'
    )
    parser.add_argument(
        '--one-shot',
        action='store_true',
        help='Run once and exit (overrides --interval)'
    )

    args = parser.parse_args()

    # Parse paths
    agents_dir = Path(args.agents_dir)
    events_dir = Path(args.events_dir) if args.events_dir else None

    # Determine mode
    interval = None if args.one_shot else args.interval

    try:
        # Create scanner
        scanner = EventFlowScanner(
            agents_dir=agents_dir,
            events_dir=events_dir,
            api_url=args.api_url,
            interval=interval
        )

        # Run
        if interval:
            scanner.run_continuous()
        else:
            results = scanner.scan_once()

            # Print summary and exit
            success_count = sum(1 for s in results.values() if s)
            total_count = len(results)

            print()
            print(f"[SCAN] Summary: {success_count}/{total_count} graphs pushed successfully")

            # Exit with appropriate code
            sys.exit(0 if success_count == total_count else 1)

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
