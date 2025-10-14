#!/usr/bin/env python3
"""
Generate Hierarchical Event Flow Tree

Creates a top-to-bottom hierarchical visualization of the event flow.

Usage:
    python tools/generate_hierarchical_tree.py
    python tools/generate_hierarchical_tree.py --output event_tree.png --format png
"""
import argparse
from pathlib import Path

import pydot

from analyze_event_flow import EventFlowAnalyzer


def generate_hierarchical_tree(analyzer: EventFlowAnalyzer, output_path: str, format: str = "png"):
    """Generate hierarchical tree using pydot with Graphviz"""

    # Create graph with hierarchical layout
    graph = pydot.Dot(graph_type='digraph', rankdir='TB', splines='ortho')

    # Set graph attributes for better readability
    graph.set_node_defaults(
        shape='box',
        style='filled,rounded',
        fontname='Segoe UI',
        fontsize='10',
        color='#cccccc'
    )

    graph.set_edge_defaults(
        arrowsize='0.8',
        color='#999999'
    )

    # Separate events and agents
    events = analyzer.get_all_events()
    agents = set(analyzer.subscriptions.keys()) | set(analyzer.publications.keys())

    # Agent color (consistent with complete graph)
    agent_color = '#ffcc80'

    # Add nodes
    for event in sorted(events):
        node = pydot.Node(
            event,
            label=event,
            fillcolor='#e0e0e0',  # Neutral grey for events without namespace
            shape='ellipse',
            fontsize='10'
        )
        graph.add_node(node)

    for agent in sorted(agents):
        node = pydot.Node(
            agent,
            label=agent.replace('_', ' '),  # Space instead of newline for better readability
            fillcolor=agent_color,
            shape='box',
            fontsize='10'
        )
        graph.add_node(node)

    # Add edges: event -> agent (subscription)
    for event, subscribers in sorted(analyzer.event_to_subscribers.items()):
        for subscriber in subscribers:
            edge = pydot.Edge(event, subscriber)
            graph.add_edge(edge)

    # Add edges: agent -> event (publication)
    for agent, publications in sorted(analyzer.publications.items()):
        for event in publications:
            edge = pydot.Edge(agent, event)
            graph.add_edge(edge)

    # Write output
    if format.lower() == 'dot':
        with open(output_path, 'w') as f:
            f.write(graph.to_string())
        print(f"✅ DOT file saved to {output_path}")
        print(f"   Generate image with: dot -Tpng {output_path} -o event_tree.png")
    else:
        # Let pydot call graphviz
        try:
            graph.write(output_path, format=format)
            print(f"✅ {format.upper()} image saved to {output_path}")
        except Exception as e:
            # Fallback: write DOT and show command
            dot_path = output_path.rsplit('.', 1)[0] + '.dot'
            with open(dot_path, 'w') as f:
                f.write(graph.to_string())
            print(f"⚠️  Could not generate {format} directly (graphviz not installed?)")
            print(f"✅ DOT file saved to {dot_path}")
            print(f"   Install graphviz: sudo apt-get install graphviz")
            print(f"   Then run: dot -T{format} {dot_path} -o {output_path}")


def generate_simplified_tree(analyzer: EventFlowAnalyzer, output_path: str, format: str = "png"):
    """Generate simplified hierarchical tree focusing on main flow"""

    graph = pydot.Dot(graph_type='digraph', rankdir='TB')

    # Set graph attributes
    graph.set_graph_defaults(
        fontname='Segoe UI',
        fontsize='12',
        splines='ortho',
        nodesep='0.5',
        ranksep='0.8'
    )

    graph.set_node_defaults(
        shape='box',
        style='filled,rounded',
        fontname='Segoe UI',
        fontsize='10',
        color='#cccccc'
    )

    graph.set_edge_defaults(
        arrowsize='0.8',
        color='#999999'
    )

    # Define main cycle flow (manual curation for clarity)
    main_flow = [
        ("START", "BotMonitoringCycleStarted", "green", "entry"),

        # Data collection phase
        ("BotMonitoringCycleStarted", "MarketPriceFetcher", "blue", "agent"),
        ("MarketPriceFetcher", "MarketPriceFetched", "blue", "event"),

        ("BotMonitoringCycleStarted", "CapitalRefresh", "blue", "agent"),
        ("CapitalRefresh", "CapitalRefreshed", "blue", "event"),

        ("BotMonitoringCycleStarted", "OpenedPositionsQuery", "blue", "agent"),
        ("OpenedPositionsQuery", "OpenedPositionsQueried", "blue", "event"),

        # Aggregation
        ("MarketPriceFetched", "DecisionContextAggregator", "purple", "agent"),
        ("CapitalRefreshed", "DecisionContextAggregator", "purple", "agent"),
        ("OpenedPositionsQueried", "DecisionContextAggregator", "purple", "agent"),
        ("DecisionContextAggregator", "DecisionContextReady", "purple", "event"),

        # Decision phase
        ("DecisionContextReady", "PoolCapitalDistribution", "orange", "agent"),
        ("PoolCapitalDistribution", "PoolCapitalCalculated", "orange", "event"),

        # Purchase flow
        ("PoolCapitalCalculated", "PurchaseInitiation", "red", "agent"),
        ("PurchaseInitiation", "PositionPurchaseInitiated", "red", "event"),
        ("PositionPurchaseInitiated", "PurchaseValidation", "red", "agent"),
        ("PurchaseValidation", "PurchaseValidated", "red", "event"),
        ("PurchaseValidated", "PurchaseExecution", "red", "agent"),
        ("PurchaseExecution", "PositionPurchased", "red", "event"),

        # Sale flow
        ("DecisionContextReady", "SaleInitiation", "cyan", "agent"),
        ("SaleInitiation", "PositionSaleInitiated", "cyan", "event"),
        ("PositionSaleInitiated", "SaleValidation", "cyan", "agent"),
        ("SaleValidation", "SaleValidated", "cyan", "event"),
        ("SaleValidated", "SaleExecution", "cyan", "agent"),
        ("SaleExecution", "PositionSold", "cyan", "event"),

        # Completion
        ("PositionPurchased", "CycleCompletionDetector", "darkgreen", "agent"),
        ("PositionSold", "CycleCompletionDetector", "darkgreen", "agent"),
        ("CycleCompletionDetector", "BotMonitoringCycleCompleted", "darkgreen", "event"),
        ("BotMonitoringCycleCompleted", "END", "green", "exit"),
    ]

    # Color map - using more muted, cohesive palette
    colors = {
        "green": {"event": "#c8e6c9", "agent": "#ffcc80", "entry": "#4caf50", "exit": "#2e7d32"},
        "blue": {"event": "#bbdefb", "agent": "#ffcc80"},
        "purple": {"event": "#e1bee7", "agent": "#ffcc80"},
        "orange": {"event": "#ffe0b2", "agent": "#ffcc80"},
        "red": {"event": "#ffcdd2", "agent": "#ffcc80"},
        "cyan": {"event": "#b2ebf2", "agent": "#ffcc80"},
        "darkgreen": {"event": "#c8e6c9", "agent": "#ffcc80"},
    }

    # Track nodes to avoid duplicates
    nodes_added = set()

    # Add nodes and edges
    for source, target, color, node_type in main_flow:
        # Add source node
        if source not in nodes_added:
            if source == "START":
                graph.add_node(pydot.Node(
                    source,
                    label="START",
                    shape="circle",
                    fillcolor=colors[color]["entry"],
                    fontcolor="white",
                    fontsize="14",
                    fontname="Segoe UI"
                ))
            else:
                # Determine node type from previous edges
                is_agent = source in [s for s, t, c, nt in main_flow if nt == "agent" and t == target]
                shape = "box" if is_agent else "ellipse"
                fill = colors.get(color, {}).get("agent" if is_agent else "event", "#f0f0f0")

                graph.add_node(pydot.Node(
                    source,
                    label=source.replace('_', ' ') if is_agent else source,
                    shape=shape,
                    fillcolor=fill,
                    fontsize='10'
                ))
            nodes_added.add(source)

        # Add target node
        if target not in nodes_added:
            if target == "END":
                graph.add_node(pydot.Node(
                    target,
                    label="END",
                    shape="circle",
                    fillcolor=colors[color]["exit"],
                    fontcolor="white",
                    fontsize="14",
                    fontname="Segoe UI"
                ))
            else:
                shape = "box" if node_type == "agent" else "ellipse"
                fill = colors[color].get(node_type, "#f0f0f0")

                graph.add_node(pydot.Node(
                    target,
                    label=target.replace('_', ' ') if node_type == "agent" else target,
                    shape=shape,
                    fillcolor=fill,
                    fontsize='10'
                ))
            nodes_added.add(target)

        # Add edge
        graph.add_edge(pydot.Edge(source, target))

    # Write output
    if format.lower() == 'dot':
        with open(output_path, 'w') as f:
            f.write(graph.to_string())
        print(f"✅ Simplified DOT file saved to {output_path}")
    else:
        try:
            graph.write(output_path, format=format)
            print(f"✅ Simplified {format.upper()} tree saved to {output_path}")
        except Exception as e:
            dot_path = output_path.rsplit('.', 1)[0] + '.dot'
            with open(dot_path, 'w') as f:
                f.write(graph.to_string())
            print(f"⚠️  Could not generate {format} directly")
            print(f"✅ DOT file saved to {dot_path}")
            print(f"   Install graphviz: sudo apt-get install graphviz")
            print(f"   Then run: dot -T{format} {dot_path} -o {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate hierarchical event flow tree")
    parser.add_argument("--output", "-o", type=str, default="event_tree.png",
                        help="Output file path (default: event_tree.png)")
    parser.add_argument("--format", "-f", choices=["png", "svg", "pdf", "dot"],
                        default="png", help="Output format (default: png)")
    parser.add_argument("--simplified", "-s", action="store_true",
                        help="Generate simplified main flow only")
    args = parser.parse_args()

    # Find agents directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    agents_dir = project_root / "python_pubsub_risk" / "agents"

    if not agents_dir.exists():
        print(f"Error: Agents directory not found at {agents_dir}")
        return 1

    # Prepare output path - if relative, put in tools directory
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = script_dir / output_path
    output_path = str(output_path)

    # Analyze
    print("Analyzing event flow...")
    analyzer = EventFlowAnalyzer(agents_dir)
    analyzer.analyze()

    # Generate tree
    if args.simplified:
        print("Generating simplified hierarchical tree...")
        generate_simplified_tree(analyzer, output_path, args.format)
    else:
        print("Generating complete hierarchical tree...")
        generate_hierarchical_tree(analyzer, output_path, args.format)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
