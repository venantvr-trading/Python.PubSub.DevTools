"""
Event Flow Visualization Server

Flask server for displaying event flow diagrams with modern UI.
"""
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Set

from flask import Flask, render_template, request, Response

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

        @app.route('/graph/<graph_type>')
        def graph(graph_type):
            return self._graph(graph_type)

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

    def _graph(self, graph_type: str):
        """Generate and serve graph SVG with filters"""
        selected_namespaces = set(request.args.getlist('namespaces'))
        hide_failed = request.args.get('hide_failed', '0') == '1'
        hide_rejected = request.args.get('hide_rejected', '0') == '1'

        if not selected_namespaces:
            event_to_namespace, _ = self._map_event_namespaces()
            selected_namespaces = set(event_to_namespace.values())

        svg_content = self._generate_graph_svg(graph_type, selected_namespaces,
                                               hide_failed, hide_rejected)
        return Response(svg_content, mimetype='image/svg+xml')

    def _generate_graph_svg(self, graph_type: str, namespaces: Set[str],
                            hide_failed: bool, hide_rejected: bool) -> bytes:
        """Generate SVG for the specified graph type"""
        analyzer = EventFlowAnalyzer(self.config.agents_dir)
        analyzer.analyze()

        self._filter_test_agents(analyzer)

        event_to_namespace, event_to_annotations = self._map_event_namespaces()

        def should_include_event(event_name: str) -> bool:
            if hide_failed:
                annotations = event_to_annotations.get(event_name, set())
                if 'failed' in annotations:
                    return False

            if hide_rejected:
                annotations = event_to_annotations.get(event_name, set())
                if 'rejection' in annotations:
                    return False

            event_ns = event_to_namespace.get(event_name, 'unknown')
            return event_ns in namespaces

        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as dot_file:
            dot_path = Path(dot_file.name)
            svg_path = dot_path.with_suffix('.svg')

            try:
                if graph_type == 'simplified':
                    from .hierarchical_tree import generate_simplified_tree

                    generate_simplified_tree(analyzer, str(dot_path), format='dot')
                elif graph_type == 'complete':
                    self._generate_complete_graph(analyzer, dot_path, event_to_namespace,
                                                  namespaces, should_include_event)
                elif graph_type == 'full-tree':
                    self._generate_full_tree(analyzer, dot_path, namespaces, should_include_event)

                result = subprocess.run(
                    ['dot', '-Tsvg', str(dot_path), '-o', str(svg_path)],
                    check=True,
                    capture_output=True,
                    text=True
                )

                svg_content = svg_path.read_bytes()
                return svg_content

            except subprocess.CalledProcessError as e:
                error_msg = f"Error generating SVG: {e.stderr}"
                return self._error_svg(error_msg)
            except FileNotFoundError:
                return self._error_svg("Graphviz not installed. Install with: sudo apt-get install graphviz")
            except Exception as e:
                return self._error_svg(f"Unexpected error: {str(e)}")
            finally:
                if dot_path.exists():
                    dot_path.unlink()
                if svg_path.exists():
                    svg_path.unlink()

    def _generate_complete_graph(self, analyzer, dot_path, event_to_namespace, namespaces, should_include_event):
        """Generate complete graph DOT file"""
        dot_content = """digraph EventFlow {
    rankdir=TB;
    node [shape=box, style="filled,rounded", fontname="Segoe UI", fontsize=10, color="#cccccc"];
    edge [arrowsize=0.8, color="#999999"];

"""
        events = {e for e in analyzer.get_all_events() if should_include_event(e)}
        connected_agents = set()

        for event in events:
            if event in analyzer.event_to_subscribers:
                connected_agents.update(analyzer.event_to_subscribers[event])

        for agent, publications in analyzer.publications.items():
            for event in publications:
                if event in events:
                    connected_agents.add(agent)
                    break

        for event in sorted(events):
            namespace = event_to_namespace.get(event, 'unknown')
            color = self._get_namespace_color(namespace)
            dot_content += f'    "{event}" [fillcolor="{color}", shape=ellipse];\n'

        for agent in sorted(connected_agents):
            dot_content += f'    "{agent}" [fillcolor="#ffcc80"];\n'

        dot_content += '\n'

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
        dot_path.write_text(dot_content)

    def _generate_full_tree(self, analyzer, dot_path, namespaces, should_include_event):
        """Generate full hierarchical tree DOT file"""
        from .hierarchical_tree import generate_hierarchical_tree

        events = {e for e in analyzer.get_all_events() if should_include_event(e)}
        connected_agents = set()

        for event in events:
            if event in analyzer.event_to_subscribers:
                connected_agents.update(analyzer.event_to_subscribers[event])

        for agent, publications in analyzer.publications.items():
            for event in publications:
                if event in events:
                    connected_agents.add(agent)
                    break

        filtered_analyzer = EventFlowAnalyzer(self.config.agents_dir)

        for agent in connected_agents:
            if agent in analyzer.subscriptions:
                filtered_subs = [e for e in analyzer.subscriptions[agent] if e in events]
                if filtered_subs:
                    filtered_analyzer.subscriptions[agent] = filtered_subs

        for agent in connected_agents:
            if agent in analyzer.publications:
                filtered_pubs = [e for e in analyzer.publications[agent] if e in events]
                if filtered_pubs:
                    filtered_analyzer.publications[agent] = filtered_pubs

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

        generate_hierarchical_tree(filtered_analyzer, str(dot_path), format='dot')

    def _error_svg(self, message: str) -> bytes:
        """Generate error SVG"""
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400">
            <text x="10" y="50" font-size="16" fill="red">{message}</text>
        </svg>'''
        return svg.encode('utf-8')

    def run(self, host: str = '0.0.0.0', debug: bool = True):
        """Run the Flask server"""
        import shutil

        print("=" * 80)
        print("🚀 Event Flow Visualization Server")
        print("=" * 80)
        print()

        if not shutil.which('dot'):
            print("❌ ERROR: Graphviz not installed!")
            print("Install with: sudo apt-get install graphviz")
            return 1

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
