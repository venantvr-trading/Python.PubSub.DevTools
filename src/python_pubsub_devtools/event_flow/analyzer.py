"""
Event Flow Analyzer

Parses all agents to extract event subscriptions and publications,
then generates a visual graph of the event flow.
"""
import re
from pathlib import Path
from typing import Dict, List, Set

from collections import defaultdict


class EventFlowAnalyzer:

    def __init__(self, agents_dir: Path):
        self.agents_dir = agents_dir
        self.subscriptions: Dict[str, List[str]] = defaultdict(list)  # agent -> [events]
        self.publications: Dict[str, List[str]] = defaultdict(list)  # agent -> [events]
        self.event_to_subscribers: Dict[str, List[str]] = defaultdict(list)  # event -> [agents]
        self.event_to_publishers: Dict[str, List[str]] = defaultdict(list)  # event -> [agents]

    def analyze(self):
        """Analyze all agent files"""
        agent_files = list(self.agents_dir.glob("*.py"))

        for agent_file in agent_files:
            if agent_file.name.startswith("__"):
                continue

            agent_name = agent_file.stem
            self._analyze_file(agent_file, agent_name)

    def _analyze_file(self, file_path: Path, agent_name: str):
        """Analyze a single agent file"""
        content = file_path.read_text()

        # Find subscriptions: self.service_bus.subscribe(EventName.__name__, ...)
        subscribe_pattern = r'self\.service_bus\.subscribe\(([A-Za-z_]+)\.__name__'
        for match in re.finditer(subscribe_pattern, content):
            event_name = match.group(1)
            self.subscriptions[agent_name].append(event_name)
            self.event_to_subscribers[event_name].append(agent_name)

        # Find publications: self.service_bus.publish(EventName.__name__, ...)
        publish_pattern = r'self\.service_bus\.publish\(([A-Za-z_]+)\.__name__'
        for match in re.finditer(publish_pattern, content):
            event_name = match.group(1)
            self.publications[agent_name].append(event_name)
            self.event_to_publishers[event_name].append(agent_name)

    def get_all_events(self) -> Set[str]:
        """Get all unique events"""
        events = set()
        events.update(self.event_to_subscribers.keys())
        events.update(self.event_to_publishers.keys())
        return events

    def get_event_chains(self) -> List[List[str]]:
        """Build event chains (sequences of events)"""
        chains = []
        visited = set()

        # Find entry point events (published but never consumed by agents)
        entry_events = []
        for event in self.event_to_publishers.keys():
            if event not in self.event_to_subscribers:
                entry_events.append(event)

        # Build chains starting from entry events
        for entry_event in entry_events:
            chain = self._build_chain(entry_event, visited)
            if chain:
                chains.append(chain)

        return chains

    def _build_chain(self, event: str, visited: Set[str]) -> List[str]:
        """Recursively build an event chain"""
        if event in visited:
            return []

        visited.add(event)
        chain = [event]

        # Find agents that subscribe to this event
        subscribers = self.event_to_subscribers.get(event, [])

        # For each subscriber, find what events they publish
        for subscriber in subscribers:
            published_events = self.publications.get(subscriber, [])
            for published_event in published_events:
                sub_chain = self._build_chain(published_event, visited)
                if sub_chain:
                    chain.extend(sub_chain)

        return chain

    def generate_mermaid(self) -> str:
        """Generate Mermaid diagram syntax"""
        lines = ["graph TD"]
        lines.append("    %% Event Flow Diagram")
        lines.append("")

        # Add all agents and events
        events = self.get_all_events()
        agents = set(self.subscriptions.keys()) | set(self.publications.keys())

        # Define node styles
        lines.append("    %% Nodes")
        for event in sorted(events):
            lines.append(f"    {event}[{event}]")
            lines.append(f"    class {event} eventNode")

        lines.append("")
        for agent in sorted(agents):
            agent_id = agent.replace("_", "")
            lines.append(f"    {agent_id}({agent})")
            lines.append(f"    class {agent_id} agentNode")

        lines.append("")
        lines.append("    %% Event Flow")

        # Add edges: event -> agent (subscription)
        for event, subscribers in sorted(self.event_to_subscribers.items()):
            for subscriber in subscribers:
                subscriber_id = subscriber.replace("_", "")
                lines.append(f"    {event} --> {subscriber_id}")

        # Add edges: agent -> event (publication)
        for agent, publications in sorted(self.publications.items()):
            agent_id = agent.replace("_", "")
            for event in publications:
                lines.append(f"    {agent_id} --> {event}")

        lines.append("")
        lines.append("    %% Styling")
        lines.append("    classDef eventNode fill:#e1f5ff,stroke:#01579b,stroke-width:2px")
        lines.append("    classDef agentNode fill:#fff3e0,stroke:#e65100,stroke-width:2px")

        return "\n".join(lines)

    def generate_graphviz(self) -> str:
        """Generate Graphviz DOT format"""
        lines = ['digraph EventFlow {']
        lines.append('    rankdir=LR;')
        lines.append('    node [shape=box];')
        lines.append('')

        events = self.get_all_events()
        agents = set(self.subscriptions.keys()) | set(self.publications.keys())

        # Define event nodes
        lines.append('    // Events')
        for event in sorted(events):
            lines.append(f'    "{event}" [style=filled, fillcolor=lightblue, shape=ellipse];')

        lines.append('')
        lines.append('    // Agents')
        for agent in sorted(agents):
            lines.append(f'    "{agent}" [style=filled, fillcolor=lightyellow];')

        lines.append('')
        lines.append('    // Event Flow')

        # Add edges
        for event, subscribers in sorted(self.event_to_subscribers.items()):
            for subscriber in subscribers:
                lines.append(f'    "{event}" -> "{subscriber}";')

        for agent, publications in sorted(self.publications.items()):
            for event in publications:
                lines.append(f'    "{agent}" -> "{event}";')

        lines.append('}')
        return '\n'.join(lines)

    def to_interactive_json(self) -> dict:
        """
        Generate JSON data for interactive visualization (React Flow format)

        Returns:
            dict: Dictionary with 'nodes' and 'edges' lists for React Flow
        """
        nodes = []
        edges = []

        events = self.get_all_events()
        agents = set(self.subscriptions.keys()) | set(self.publications.keys())

        # Create event nodes
        for event in sorted(events):
            nodes.append({
                'id': event,
                'type': 'event',
                'data': {'label': event},
                'position': {'x': 0, 'y': 0}  # Will be positioned by React Flow
            })

        # Create agent nodes
        for agent in sorted(agents):
            nodes.append({
                'id': agent,
                'type': 'agent',
                'data': {'label': agent},
                'position': {'x': 0, 'y': 0}  # Will be positioned by React Flow
            })

        # Create edges for subscriptions (event -> agent)
        for event, subscribers in self.event_to_subscribers.items():
            for subscriber in subscribers:
                edges.append({
                    'id': f"{event}-to-{subscriber}",
                    'source': event,
                    'target': subscriber,
                    'type': 'subscription',
                    'animated': False
                })

        # Create edges for publications (agent -> event)
        for agent, publications in self.publications.items():
            for event in publications:
                edges.append({
                    'id': f"{agent}-to-{event}",
                    'source': agent,
                    'target': event,
                    'type': 'publication',
                    'animated': True  # Animated to show publication direction
                })

        return {
            'nodes': nodes,
            'edges': edges
        }

    def print_summary(self):
        """Print a text summary of the event flow"""
        print("=" * 80)
        print("EVENT FLOW ANALYSIS")
        print("=" * 80)
        print()

        events = self.get_all_events()
        agents = set(self.subscriptions.keys()) | set(self.publications.keys())

        print(f"Total Events: {len(events)}")
        print(f"Total Agents: {len(agents)}")
        print()

        print("-" * 80)
        print("EVENTS → SUBSCRIBERS → PUBLISHERS")
        print("-" * 80)

        for event in sorted(events):
            subscribers = self.event_to_subscribers.get(event, [])
            publishers = self.event_to_publishers.get(event, [])

            print(f"\n📌 {event}")

            if publishers:
                print(f"   Published by: {', '.join(sorted(publishers))}")
            else:
                print(f"   Published by: [EXTERNAL/ORCHESTRATOR]")

            if subscribers:
                print(f"   Consumed by:  {', '.join(sorted(subscribers))}")
            else:
                print(f"   Consumed by:  [NO SUBSCRIBERS]")

        print()
        print("-" * 80)
        print("AGENT EVENT MATRIX")
        print("-" * 80)

        for agent in sorted(agents):
            subscribed = self.subscriptions.get(agent, [])
            published = self.publications.get(agent, [])

            print(f"\n🤖 {agent}")
            if subscribed:
                print(f"   Listens to: {', '.join(sorted(subscribed))}")
            if published:
                print(f"   Publishes:  {', '.join(sorted(published))}")
