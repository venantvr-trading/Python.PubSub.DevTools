"""
Event Flow Visualization Server

Flask server for displaying event flow diagrams with modern UI.
"""
import re
from pathlib import Path
from typing import Dict

from flask import Flask, render_template, request, jsonify

from .analyzer import EventFlowAnalyzer
from ..config import EventFlowConfig


class EventFlowServer:
    """Flask server for event flow visualization"""

    def __init__(self, config: EventFlowConfig):
        """
        Initialize server with configuration

        Args:
            config: EventFlowConfig with agents_dir, events_dir, port, etc.
        """
        self.config = config
        self.app = self._create_app()

    def _create_app(self) -> Flask:
        """Create and configure Flask app"""
        # Get package root for web assets
        package_root = Path(__file__).parent.parent
        app = Flask(__name__,
                    template_folder=str(package_root / 'web' / 'templates'),
                    static_folder=str(package_root / 'web' / 'static'))

        # Register routes
        @app.route('/')
        def index():
            return self._index()

        @app.route('/api/graph-data/<graph_type>')
        def api_graph_data(graph_type: str):
            """Provide graph data in JSON format for React Flow"""
            return self._api_graph_data(graph_type)

        @app.route('/api/generate-prompt', methods=['POST'])
        def api_generate_prompt():
            """Generate LLM prompt for graph modifications"""
            return self._api_generate_prompt()

        return app

    def _map_event_namespaces(self) -> tuple[Dict[str, str], Dict[str, set]]:
        """Map events to their namespaces and annotations"""
        import sys
        import importlib.util

        event_to_namespace = {}
        event_to_annotations = {}

        if not self.config.events_dir.exists():
            return event_to_namespace, event_to_annotations

        # Add events dir to sys.path temporarily
        events_parent = str(self.config.events_dir.parent)
        if events_parent not in sys.path:
            sys.path.insert(0, events_parent)

        for namespace_dir in self.config.events_dir.iterdir():
            if not namespace_dir.is_dir() or namespace_dir.name.startswith("__"):
                continue

            namespace = namespace_dir.name

            for event_file in namespace_dir.glob("*.py"):
                if event_file.name.startswith("__"):
                    continue

                try:
                    module_name = f"events.{namespace}.{event_file.stem}"
                    spec = importlib.util.spec_from_file_location(module_name, event_file)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if isinstance(attr, type) and hasattr(attr, '__bases__'):
                                if attr_name[0].isupper() and not attr_name.startswith('_'):
                                    event_to_namespace[attr_name] = namespace

                                    if hasattr(attr, '__event_annotation__'):
                                        annotation = attr.__event_annotation__
                                        if annotation:
                                            event_to_annotations[attr_name] = {annotation}

                except Exception:
                    # Fallback to regex
                    content = event_file.read_text()
                    class_pattern = r'class ([A-Z][A-Za-z0-9_]+)\(.*?BaseModel\)'
                    for match in re.finditer(class_pattern, content):
                        event_name = match.group(1)
                        event_to_namespace[event_name] = namespace

        return event_to_namespace, event_to_annotations

    def _get_namespace_color(self, namespace: str) -> str:
        """Get color for a namespace"""
        return self.config.namespace_colors.get(namespace,
                                                self.config.namespace_colors.get('unknown', '#e0e0e0'))

    def _filter_test_agents(self, analyzer: EventFlowAnalyzer):
        """Remove test agents from analyzer"""
        for test_agent in self.config.test_agents:
            if test_agent in analyzer.subscriptions:
                for event in analyzer.subscriptions[test_agent]:
                    if event in analyzer.event_to_subscribers:
                        analyzer.event_to_subscribers[event] = [
                            a for a in analyzer.event_to_subscribers[event] if a != test_agent
                        ]
                del analyzer.subscriptions[test_agent]

            if test_agent in analyzer.publications:
                for event in analyzer.publications[test_agent]:
                    if event in analyzer.event_to_publishers:
                        analyzer.event_to_publishers[event] = [
                            a for a in analyzer.event_to_publishers[event] if a != test_agent
                        ]
                del analyzer.publications[test_agent]

    def _index(self):
        """Main page with tabs and filters"""
        analyzer = EventFlowAnalyzer(self.config.agents_dir)
        analyzer.analyze()

        self._filter_test_agents(analyzer)

        events = analyzer.get_all_events()
        agents = set(analyzer.subscriptions.keys()) | set(analyzer.publications.keys())

        event_to_namespace, _ = self._map_event_namespaces()
        namespaces = sorted(set(event_to_namespace.values()))

        total_connections = 0
        for event, subs in analyzer.event_to_subscribers.items():
            total_connections += len([s for s in subs if s not in self.config.test_agents])
        for agent, pubs in analyzer.publications.items():
            if agent not in self.config.test_agents:
                total_connections += len(pubs)

        return render_template(
            'event_flow.html',
            total_events=len(events),
            total_agents=len(agents),
            total_connections=total_connections,
            total_namespaces=len(namespaces),
            namespaces=namespaces,
            namespace_colors=self.config.namespace_colors
        )

    def _api_graph_data(self, graph_type: str):
        """API endpoint to provide graph data in JSON format for React Flow"""
        analyzer = EventFlowAnalyzer(self.config.agents_dir)
        analyzer.analyze()
        self._filter_test_agents(analyzer)

        # For now, return the same data for all graph types
        # You can add filtering logic here later for 'simplified' vs 'complete'
        return jsonify(analyzer.to_interactive_json())

    def _api_generate_prompt(self):
        """API endpoint to generate LLM prompts for graph modifications"""
        data = request.json
        action = data.get('action')
        event = data.get('event')
        agent = data.get('agent')

        analyzer = EventFlowAnalyzer(self.config.agents_dir)
        analyzer.analyze()

        if action == 'add_subscription':
            prompt = self._generate_add_subscription_prompt(event, agent, analyzer)
        elif action == 'remove_subscription':
            prompt = self._generate_remove_subscription_prompt(event, agent, analyzer)
        else:
            prompt = "Action non supportée pour le moment."

        return jsonify({'prompt': prompt})

    def _generate_add_subscription_prompt(self, event: str, agent: str, analyzer: EventFlowAnalyzer) -> str:
        """Generate prompt for adding a subscription"""
        publishers = analyzer.event_to_publishers.get(event, [])
        existing_subscribers = analyzer.event_to_subscribers.get(event, [])

        prompt = f"""# Task: Add Event Subscription

## Objective
Make the agent `{agent}` subscribe to the event `{event}`.

## Context
- **Event**: `{event}`
- **Current Publishers**: {', '.join(publishers) if publishers else 'None (external event)'}
- **Current Subscribers**: {', '.join(existing_subscribers) if existing_subscribers else 'None'}

## Implementation Steps
1. Locate the `{agent}` agent file in the agents directory
2. Add the following subscription in the agent's initialization:
   ```python
   self.service_bus.subscribe({event}.__name__, self._handle_{event.lower()})
   ```
3. Implement the event handler:
   ```python
   async def _handle_{event.lower()}(self, event_data: {event}):
       # TODO: Implement event handling logic
       pass
   ```
4. Ensure the event class is imported at the top of the file
5. Test the subscription to verify it works correctly

## Notes
- This is a new subscription, so you're adding functionality to `{agent}`
- Consider what this agent should do when receiving `{event}`
"""
        return prompt

    def _generate_remove_subscription_prompt(self, event: str, agent: str, analyzer: EventFlowAnalyzer) -> str:
        """Generate prompt for removing a subscription"""
        prompt = f"""# Task: Remove Event Subscription

## Objective
Remove the subscription of agent `{agent}` to the event `{event}`.

## Context
- **Event**: `{event}`
- **Agent**: `{agent}`

## Implementation Steps
1. Locate the `{agent}` agent file in the agents directory
2. Remove or comment out the subscription:
   ```python
   # self.service_bus.subscribe({event}.__name__, self._handle_{event.lower()})
   ```
3. Optionally remove the associated event handler method `_handle_{event.lower()}`
4. Remove the import for `{event}` if it's no longer used
5. Test to ensure the agent no longer receives `{event}` events

## Notes
- This removes existing functionality from `{agent}`
- Ensure this doesn't break any critical business logic
"""
        return prompt

    def run(self, host: str = '0.0.0.0', debug: bool = True):
        """Run the Flask server"""
        print("=" * 80)
        print("🚀 Event Flow Visualization Server (React Flow)")
        print("=" * 80)
        print()

        if not self.config.agents_dir.exists():
            print(f"❌ Error: Agents directory not found at {self.config.agents_dir}")
            return 1

        analyzer = EventFlowAnalyzer(self.config.agents_dir)
        analyzer.analyze()
        self._filter_test_agents(analyzer)

        events = analyzer.get_all_events()
        agents = set(analyzer.subscriptions.keys()) | set(analyzer.publications.keys())
        event_to_namespace, _ = self._map_event_namespaces()
        namespaces = set(event_to_namespace.values())

        print(f"   ✅ {len(events)} events")
        print(f"   ✅ {len(agents)} agents (excluding {len(self.config.test_agents)} test agents)")
        print(f"   ✅ {len(namespaces)} namespaces")
        print()
        print("🌐 Starting web server...")
        print(f"   📍 Open in browser: http://localhost:{self.config.port}")
        print("   Press Ctrl+C to stop")
        print("=" * 80)
        print()

        self.app.run(host=host, port=self.config.port, debug=debug)
        return 0
