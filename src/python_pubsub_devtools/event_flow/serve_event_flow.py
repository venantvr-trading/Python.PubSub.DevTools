#!/usr/bin/env python3
"""
Event Flow Visualization Server

Launches a web server that displays event flow diagrams in real-time with a modern UI.

Usage:
    python tools/serve_event_flow.py
    make docs-serve
"""
import re
import subprocess
from pathlib import Path
from typing import Dict, Set

from flask import Flask, render_template, request

# Configure Flask to find templates and static files in web directory
WEB_DIR = Path(__file__).parent.parent / 'web'
app = Flask(__name__,
            template_folder=str(WEB_DIR / 'templates'),
            static_folder=str(WEB_DIR / 'static'))

# Find project paths
SCRIPT_DIR = Path(__file__).parent  # tools/event_flow
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # Python.PubSub.Risk
AGENTS_DIR = PROJECT_ROOT / "python_pubsub_risk" / "agents"
EVENTS_DIR = PROJECT_ROOT / "python_pubsub_risk" / "events"

# Test agents to exclude from graph (agents used only in tests)
TEST_AGENTS = {
    'token_balance_refresh',
}

# Namespace colors
NAMESPACE_COLORS = {
    'bot_lifecycle': '#81c784',  # green
    'market_data': '#64b5f6',  # blue
    'indicator': '#9575cd',  # purple
    'internal': '#ba68c8',  # purple light
    'capital': '#ffd54f',  # yellow
    'pool': '#ffb74d',  # orange
    'position': '#ff8a65',  # deep orange
    'exchange': '#4dd0e1',  # cyan
    'command': '#a1887f',  # brown
    'database': '#90a4ae',  # blue grey
    'exit_strategy': '#aed581',  # light green
    'query': '#81d4fa',  # light blue
    'unknown': '#e0e0e0',  # grey
}


def map_event_namespaces() -> tuple[Dict[str, str], Dict[str, set]]:
    """Map events to their namespaces and annotations by scanning event directories

    Returns:
        (event_to_namespace, event_to_annotations)
    """
    import sys
    import importlib.util

    event_to_namespace = {}
    event_to_annotations = {}

    if not EVENTS_DIR.exists():
        return event_to_namespace, event_to_annotations

    # Add events dir to sys.path temporarily
    events_parent = str(EVENTS_DIR.parent)
    if events_parent not in sys.path:
        sys.path.insert(0, events_parent)

    for namespace_dir in EVENTS_DIR.iterdir():
        if not namespace_dir.is_dir() or namespace_dir.name.startswith("__") or namespace_dir.name == "__pycache__":
            continue

        namespace = namespace_dir.name

        # Scan Python files in namespace
        for event_file in namespace_dir.glob("*.py"):
            if event_file.name.startswith("__"):
                continue

            # Try to import the module and inspect classes
            try:
                module_name = f"events.{namespace}.{event_file.stem}"
                spec = importlib.util.spec_from_file_location(module_name, event_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Inspect all classes in the module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        # Check if it's a class and has BaseModel in its bases
                        if isinstance(attr, type) and hasattr(attr, '__bases__'):
                            # Check if it looks like an event class (uppercase name)
                            if attr_name[0].isupper() and not attr_name.startswith('_'):
                                event_to_namespace[attr_name] = namespace

                                # Check for annotation decorator
                                if hasattr(attr, '__event_annotation__'):
                                    annotation = attr.__event_annotation__
                                    if annotation:
                                        event_to_annotations[attr_name] = {annotation}

            except Exception as e:
                # If import fails, fall back to regex parsing
                content = event_file.read_text()
                class_pattern = r'class ([A-Z][A-Za-z0-9_]+)\(.*?BaseModel\)'
                for match in re.finditer(class_pattern, content):
                    event_name = match.group(1)
                    event_to_namespace[event_name] = namespace

    return event_to_namespace, event_to_annotations


def get_namespace_color(namespace: str) -> str:
    """Get color for a namespace"""
    return NAMESPACE_COLORS.get(namespace, NAMESPACE_COLORS['unknown'])


def generate_graph_svg(graph_type: str, namespaces: Set[str], hide_failed: bool, hide_rejected: bool) -> bytes:
    """Generate SVG for the specified graph type with filters"""
    import sys
    import tempfile

    # Add event_flow dir to path for imports
    sys.path.insert(0, str(SCRIPT_DIR))

    from analyze_event_flow import EventFlowAnalyzer

    # Analyze event flow
    print(f"Analyzing event flow for {graph_type}...")
    analyzer = EventFlowAnalyzer(AGENTS_DIR)
    analyzer.analyze()

    # Filter out test agents from analyzer
    for test_agent in TEST_AGENTS:
        # Remove from subscriptions
        if test_agent in analyzer.subscriptions:
            # Remove agent from event_to_subscribers
            for event in analyzer.subscriptions[test_agent]:
                if event in analyzer.event_to_subscribers:
                    analyzer.event_to_subscribers[event] = [
                        a for a in analyzer.event_to_subscribers[event] if a != test_agent
                    ]
            del analyzer.subscriptions[test_agent]

        # Remove from publications
        if test_agent in analyzer.publications:
            # Remove agent from event_to_publishers
            for event in analyzer.publications[test_agent]:
                if event in analyzer.event_to_publishers:
                    analyzer.event_to_publishers[event] = [
                        a for a in analyzer.event_to_publishers[event] if a != test_agent
                    ]
            del analyzer.publications[test_agent]

    # Get event namespace and annotation mappings
    event_to_namespace, event_to_annotations = map_event_namespaces()

    # Filter events based on selected namespaces, hide_failed, and hide_rejected options
    def should_include_event(event_name: str) -> bool:
        # Check if event should be hidden (Failed events with @failed annotation)
        if hide_failed:
            annotations = event_to_annotations.get(event_name, set())
            if 'failed' in annotations:
                return False

        # Check if event should be hidden (Rejected events with @rejection annotation)
        if hide_rejected:
            annotations = event_to_annotations.get(event_name, set())
            if 'rejection' in annotations:
                return False

        # Check namespace filter
        event_ns = event_to_namespace.get(event_name, 'unknown')
        return event_ns in namespaces

    # Create temp files for DOT and SVG
    temp_dir = Path(tempfile.gettempdir())
    dot_file = temp_dir / f"event_flow_{graph_type}.dot"
    svg_file = temp_dir / f"event_flow_{graph_type}.svg"

    try:
        # Generate DOT based on type
        if graph_type == 'simplified':
            print("Generating simplified tree...")
            from generate_hierarchical_tree import generate_simplified_tree

            generate_simplified_tree(analyzer, str(dot_file), format='dot')
        elif graph_type == 'complete':
            print("Generating complete graph...")
            # Generate complete graph with filtered events and namespace colors
            dot_content = """digraph EventFlow {
    rankdir=TB;
    node [shape=box, style="filled,rounded", fontname="Segoe UI", fontsize=10, color="#cccccc"];
    edge [arrowsize=0.8, color="#999999"];

"""
            # Filter events
            events = {e for e in analyzer.get_all_events() if should_include_event(e)}

            # Filter agents: keep only those connected to visible events
            connected_agents = set()

            # Find agents that subscribe to visible events
            for event in events:
                if event in analyzer.event_to_subscribers:
                    connected_agents.update(analyzer.event_to_subscribers[event])

            # Find agents that publish visible events
            for agent, publications in analyzer.publications.items():
                for event in publications:
                    if event in events:
                        connected_agents.add(agent)
                        break

            # Add event nodes with namespace colors
            for event in sorted(events):
                namespace = event_to_namespace.get(event, 'unknown')
                color = get_namespace_color(namespace)
                dot_content += f'    "{event}" [fillcolor="{color}", shape=ellipse];\n'

            # Add agent nodes (only connected ones)
            for agent in sorted(connected_agents):
                dot_content += f'    "{agent}" [fillcolor="#ffcc80"];\n'

            dot_content += '\n'

            # Add edges (only for filtered events and connected agents)
            for event, subscribers in sorted(analyzer.event_to_subscribers.items()):
                if event not in events:
                    continue
                for subscriber in subscribers:
                    if subscriber in connected_agents:
                        dot_content += f'    "{event}" -> "{subscriber}";\n'

            for agent, publications in sorted(analyzer.publications.items()):
                if agent not in connected_agents:
                    continue
                for event in publications:
                    if event not in events:
                        continue
                    dot_content += f'    "{agent}" -> "{event}";\n'

            dot_content += '}\n'
            dot_file.write_text(dot_content)
        elif graph_type == 'full-tree':
            print("Generating full hierarchy tree...")
            from generate_hierarchical_tree import generate_hierarchical_tree

            # Apply filters to full-tree like we do for complete graph
            # Filter events
            events = {e for e in analyzer.get_all_events() if should_include_event(e)}

            # Filter agents: keep only those connected to visible events
            connected_agents = set()

            # Find agents that subscribe to visible events
            for event in events:
                if event in analyzer.event_to_subscribers:
                    connected_agents.update(analyzer.event_to_subscribers[event])

            # Find agents that publish visible events
            for agent, publications in analyzer.publications.items():
                for event in publications:
                    if event in events:
                        connected_agents.add(agent)
                        break

            # Create a filtered copy of the analyzer
            filtered_analyzer = EventFlowAnalyzer(AGENTS_DIR)

            # Copy only filtered subscriptions
            for agent in connected_agents:
                if agent in analyzer.subscriptions:
                    filtered_subs = [e for e in analyzer.subscriptions[agent] if e in events]
                    if filtered_subs:
                        filtered_analyzer.subscriptions[agent] = filtered_subs

            # Copy only filtered publications
            for agent in connected_agents:
                if agent in analyzer.publications:
                    filtered_pubs = [e for e in analyzer.publications[agent] if e in events]
                    if filtered_pubs:
                        filtered_analyzer.publications[agent] = filtered_pubs

            # Rebuild event_to_subscribers and event_to_publishers for filtered analyzer
            for agent, subs in filtered_analyzer.subscriptions.items():
                for event in subs:
                    if event not in filtered_analyzer.event_to_subscribers:
                        filtered_analyzer.event_to_subscribers[event] = []
                    filtered_analyzer.event_to_subscribers[event].append(agent)

            for agent, pubs in filtered_analyzer.publications.items():
                for event in pubs:
                    if event not in filtered_analyzer.event_to_publishers:
                        filtered_analyzer.event_to_publishers[event] = []
                    filtered_analyzer.event_to_publishers[event].append(agent)

            generate_hierarchical_tree(filtered_analyzer, str(dot_file), format='dot')

        print(f"DOT file created: {dot_file}")

        # Convert DOT to SVG using Graphviz
        print(f"Converting to SVG with Graphviz...")
        result = subprocess.run(
            ['dot', '-Tsvg', str(dot_file), '-o', str(svg_file)],
            check=True,
            capture_output=True,
            text=True
        )

        print(f"SVG created: {svg_file}")

        # Read SVG content
        svg_content = svg_file.read_bytes()

        return svg_content

    except subprocess.CalledProcessError as e:
        error_msg = f"Error generating SVG: {e.stderr}"
        print(error_msg)
        svg_content = f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400"><text x="10" y="50" font-size="16" fill="red">{error_msg}</text><text x="10" y="80">Install graphviz: sudo apt-get install graphviz</text></svg>'
        return svg_content.encode('utf-8')
    except FileNotFoundError as e:
        error_msg = "Graphviz not found"
        print(error_msg)
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400"><text x="10" y="50" font-size="16" fill="red">Graphviz not installed</text><text x="10" y="80">Install with: sudo apt-get install graphviz</text></svg>'
        return svg_content.encode('utf-8')
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        import traceback

        traceback.print_exc()
        svg_content = f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400"><text x="10" y="50" font-size="16" fill="red">{error_msg}</text></svg>'
        return svg_content.encode('utf-8')
    finally:
        # Cleanup temp files
        if dot_file.exists():
            dot_file.unlink()
        if svg_file.exists():
            svg_file.unlink()


@app.route('/')
def index():
    """Main page with tabs and filters"""
    from analyze_event_flow import EventFlowAnalyzer

    # Analyze to get stats
    analyzer = EventFlowAnalyzer(AGENTS_DIR)
    analyzer.analyze()

    # Filter out test agents
    for test_agent in TEST_AGENTS:
        if test_agent in analyzer.subscriptions:
            del analyzer.subscriptions[test_agent]
        if test_agent in analyzer.publications:
            del analyzer.publications[test_agent]

    events = analyzer.get_all_events()
    agents = set(analyzer.subscriptions.keys()) | set(analyzer.publications.keys())

    # Get namespaces
    event_to_namespace, _ = map_event_namespaces()
    namespaces = sorted(set(event_to_namespace.values()))

    # Count connections (excluding test agents)
    total_connections = 0
    for event, subs in analyzer.event_to_subscribers.items():
        total_connections += len([s for s in subs if s not in TEST_AGENTS])
    for agent, pubs in analyzer.publications.items():
        if agent not in TEST_AGENTS:
            total_connections += len(pubs)

    return render_template(
        'event_flow.html',
        total_events=len(events),
        total_agents=len(agents),
        total_connections=total_connections,
        total_namespaces=len(namespaces),
        namespaces=namespaces,
        namespace_colors=NAMESPACE_COLORS
    )


@app.route('/graph/<graph_type>')
def graph(graph_type):
    """Generate and serve graph SVG with filters"""
    from flask import Response

    # Get filters from query parameters
    selected_namespaces = set(request.args.getlist('namespaces'))
    hide_failed = request.args.get('hide_failed', '0') == '1'
    hide_rejected = request.args.get('hide_rejected', '0') == '1'

    # If no namespaces selected, use all
    if not selected_namespaces:
        event_to_namespace, _ = map_event_namespaces()
        selected_namespaces = set(event_to_namespace.values())

    svg_content = generate_graph_svg(graph_type, selected_namespaces, hide_failed, hide_rejected)
    return Response(svg_content, mimetype='image/svg+xml')


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Event Flow Visualization Server")
    parser.add_argument("--port", type=int, default=5555, help="Port to run server on (default: 5555)")
    parser.add_argument("--agents-dir", type=str, help="Path to agents directory")
    parser.add_argument("--events-dir", type=str, help="Path to events directory")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    args = parser.parse_args()

    # Update global paths if provided
    global AGENTS_DIR, EVENTS_DIR
    if args.agents_dir:
        AGENTS_DIR = Path(args.agents_dir)
    if args.events_dir:
        EVENTS_DIR = Path(args.events_dir)

    print("=" * 80)
    print("🚀 Event Flow Visualization Server")
    print("=" * 80)
    print()

    # Check Graphviz
    import shutil

    if not shutil.which('dot'):
        print("❌ ERROR: Graphviz not installed!")
        print()
        print("Install with:")
        print("  sudo apt-get install graphviz")
        print()
        print("Or on macOS:")
        print("  brew install graphviz")
        print()
        return 1

    print("📊 Analyzing event flow...")
    print(f"   Agents directory: {AGENTS_DIR}")
    print(f"   Events directory: {EVENTS_DIR}")
    print()

    # Quick check
    if not AGENTS_DIR.exists():
        print(f"❌ Error: Agents directory not found at {AGENTS_DIR}")
        return 1

    from analyze_event_flow import EventFlowAnalyzer

    analyzer = EventFlowAnalyzer(AGENTS_DIR)
    analyzer.analyze()

    # Filter out test agents
    for test_agent in TEST_AGENTS:
        if test_agent in analyzer.subscriptions:
            del analyzer.subscriptions[test_agent]
        if test_agent in analyzer.publications:
            del analyzer.publications[test_agent]

    events = analyzer.get_all_events()
    agents = set(analyzer.subscriptions.keys()) | set(analyzer.publications.keys())

    # Get namespaces
    event_to_namespace, _ = map_event_namespaces()
    namespaces = set(event_to_namespace.values())

    print(f"   ✅ {len(events)} events")
    print(f"   ✅ {len(agents)} agents (excluding {len(TEST_AGENTS)} test agents)")
    print(f"   ✅ {len(namespaces)} namespaces")
    print()
    print("🌐 Starting web server...")
    print()
    print(f"   📍 Open in browser: http://{args.host}:{args.port}")
    print()
    print("   Press Ctrl+C to stop")
    print("=" * 80)
    print()

    app.run(host=args.host, port=args.port, debug=True)


if __name__ == '__main__':
    main()