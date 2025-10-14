#!/usr/bin/env python3
"""
Generate Event Flow Image using matplotlib and networkx

This script generates a visual representation of the event flow
without requiring graphviz to be installed.

Usage:
    python tools/generate_event_flow_image.py
    python tools/generate_event_flow_image.py --output event_flow.png
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

from analyze_event_flow import EventFlowAnalyzer


class EventFlowImageGenerator:
    """Generates visual event flow images using matplotlib and networkx"""

    def __init__(self, analyzer: EventFlowAnalyzer, title: str = "Event Flow Diagram"):
        """Initialize image generator

        Args:
            analyzer: EventFlowAnalyzer instance with analyzed data
            title: Title for the generated image
        """
        self.analyzer = analyzer
        self.title = title

    def generate_image(self, output_path: str, layout: str = "spring"):
        """Generate a visual graph using matplotlib and networkx

        Args:
            output_path: Path where to save the generated image
            layout: Graph layout algorithm (spring, kamada, circular, hierarchical)
        """
        # Create directed graph
        G = nx.DiGraph()

        # Add nodes
        events = self.analyzer.get_all_events()
        agents = set(self.analyzer.subscriptions.keys()) | set(self.analyzer.publications.keys())

        # Add event nodes
        for event in events:
            G.add_node(event, node_type='event')

        # Add agent nodes
        for agent in agents:
            G.add_node(agent, node_type='agent')

        # Add edges: event -> agent (subscription)
        for event, subscribers in self.analyzer.event_to_subscribers.items():
            for subscriber in subscribers:
                G.add_edge(event, subscriber, edge_type='consume')

        # Add edges: agent -> event (publication)
        for agent, publications in self.analyzer.publications.items():
            for event in publications:
                G.add_edge(agent, event, edge_type='publish')

        # Choose layout
        if layout == "spring":
            pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
        elif layout == "kamada":
            pos = nx.kamada_kawai_layout(G)
        elif layout == "circular":
            pos = nx.circular_layout(G)
        elif layout == "hierarchical":
            # Hierarchical layout (top to bottom)
            pos = nx.nx_agraph.graphviz_layout(G, prog='dot') if hasattr(nx, 'nx_agraph') else nx.spring_layout(G)
        else:
            pos = nx.spring_layout(G, seed=42)

        # Create figure with high DPI for better quality
        plt.figure(figsize=(24, 18), dpi=150)

        # Separate nodes by type
        event_nodes = [node for node, data in G.nodes(data=True) if data.get('node_type') == 'event']
        agent_nodes = [node for node, data in G.nodes(data=True) if data.get('node_type') == 'agent']

        # Draw event nodes (ellipses, blue)
        nx.draw_networkx_nodes(
            G, pos,
            nodelist=event_nodes,
            node_color='lightblue',
            node_size=2000,
            node_shape='o',
            alpha=0.9,
            linewidths=2,
            edgecolors='darkblue'
        )

        # Draw agent nodes (rectangles, yellow)
        nx.draw_networkx_nodes(
            G, pos,
            nodelist=agent_nodes,
            node_color='lightyellow',
            node_size=2000,
            node_shape='s',
            alpha=0.9,
            linewidths=2,
            edgecolors='darkorange'
        )

        # Draw edges
        nx.draw_networkx_edges(
            G, pos,
            edge_color='gray',
            arrows=True,
            arrowsize=15,
            arrowstyle='->',
            width=1.5,
            alpha=0.6,
            connectionstyle='arc3,rad=0.1'
        )

        # Draw labels
        nx.draw_networkx_labels(
            G, pos,
            font_size=6,
            font_weight='bold',
            font_family='sans-serif'
        )

        # Add legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightblue',
                       markersize=10, label='Event', markeredgecolor='darkblue', markeredgewidth=2),
            plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='lightyellow',
                       markersize=10, label='Agent', markeredgecolor='darkorange', markeredgewidth=2),
        ]
        plt.legend(handles=legend_elements, loc='upper right', fontsize=12)

        plt.title(self.title, fontsize=20, fontweight='bold', pad=20)
        plt.axis('off')
        plt.tight_layout()

        # Save
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"✅ Image saved to {output_path}")
        print(f"   - {len(event_nodes)} events (blue circles)")
        print(f"   - {len(agent_nodes)} agents (yellow squares)")
        print(f"   - {G.number_of_edges()} connections")


def main():
    parser = argparse.ArgumentParser(description="Generate event flow image")
    parser.add_argument("--agents-dir", type=str, help="Path to agents directory")
    parser.add_argument("--output", "-o", type=str, default="event_flow.png",
                        help="Output image path (default: event_flow.png)")
    parser.add_argument("--layout", choices=["spring", "kamada", "circular", "hierarchical"],
                        default="spring", help="Graph layout algorithm (default: spring)")
    parser.add_argument("--title", type=str, default="Event Flow Diagram",
                        help="Title for the diagram (default: Event Flow Diagram)")
    args = parser.parse_args()

    # Determine agents directory
    if args.agents_dir:
        agents_dir = Path(args.agents_dir)
    else:
        # Default: infer from project structure
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent
        agents_dir = project_root / "python_pubsub_risk" / "agents"

    if not agents_dir.exists():
        print(f"Error: Agents directory not found at {agents_dir}")
        return 1

    # Analyze
    print(f"Analyzing event flow from {agents_dir}...")
    analyzer = EventFlowAnalyzer(agents_dir)
    analyzer.analyze()

    # Generate image
    print(f"Generating image with {args.layout} layout...")
    generator = EventFlowImageGenerator(analyzer, title=args.title)
    generator.generate_image(args.output, args.layout)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
