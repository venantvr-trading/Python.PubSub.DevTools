"""
Event Flow Visualization Server

Launches a web server that displays event flow diagrams in real-time with a modern UI.

Usage:
    python tools/serve_event_flow.py
    make docs-serve
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from flask import Flask, render_template, request, jsonify, Response

# Import storage
from .storage import get_storage, initialize_storage, GraphData


# Namespace colors (used for UI display) - could be moved to config
# NAMESPACE_COLORS = {
#     'bot_lifecycle': '#81c784',  # green
#     'market_data': '#64b5f6',  # blue
#     'indicator': '#9575cd',  # purple
#     'internal': '#ba68c8',  # purple light
#     'capital': '#ffd54f',  # yellow
#     'pool': '#ffb74d',  # orange
#     'position': '#ff8a65',  # deep orange
#     'exchange': '#4dd0e1',  # cyan
#     'command': '#a1887f',  # brown
#     'database': '#90a4ae',  # blue grey
#     'exit_strategy': '#aed581',  # light green
#     'query': '#81d4fa',  # light blue
#     'unknown': '#e0e0e0',  # grey
# }


# def get_namespace_color(namespace: str) -> str:
#     """Get color for a namespace"""
#     return NAMESPACE_COLORS.get(namespace, NAMESPACE_COLORS['unknown'])


def _convert_dot_to_svg(dot_content: str, graph_type: str) -> bytes | None:
    """
    Convert DOT content to SVG using Graphviz
    """
    import tempfile

    temp_dir = Path(tempfile.gettempdir())
    dot_file = temp_dir / f"cached_{graph_type}.dot"
    svg_file = temp_dir / f"cached_{graph_type}.svg"

    try:
        dot_file.write_text(dot_content, encoding='utf-8')
        subprocess.run(
            ['dot', '-Tsvg', str(dot_file), '-o', str(svg_file)],
            check=True, capture_output=True, text=True, timeout=30
        )
        return svg_file.read_bytes()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, Exception) as e:
        print(f"Error converting DOT to SVG: {e}")
        return None
    finally:
        if dot_file.exists(): dot_file.unlink()
        if svg_file.exists(): svg_file.unlink()


def _filter_dot_content(dot_content: str, namespaces: list[str], keywords: list[str]) -> str:
    """
    Filtre le contenu DOT en ne gardant que les nœuds et arêtes pertinents.
    """
    lines = dot_content.splitlines()
    header_lines = []
    node_definitions = {}
    edge_lines = []

    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith(('digraph', 'graph', 'rankdir', 'node', 'edge')):
            header_lines.append(line)
        elif '->' in stripped_line:
            edge_lines.append(stripped_line)
        elif '[' in stripped_line and ']' in stripped_line:
            match = re.search(r'"([^"]+)"', stripped_line)
            if match:
                node_definitions[match.group(1)] = line

    # --- LOGIQUE DE FILTRAGE CORRIGÉE ---

    # 1. Sélectionner les nœuds (agents + événements) dont le namespace est coché
    initial_nodes_to_keep = set()
    attr_pattern = re.compile(r'\[(.*?)\]')

    for node_name, definition_line in node_definitions.items():
        attr_match = attr_pattern.search(definition_line)
        if not attr_match: continue
        attributes = attr_match.group(1)

        # Le namespace est stocké dans class="namespace-xxx" pour tous les nœuds (agents et événements)
        class_match = re.search(r'class="namespace-([^"]+)"', attributes)
        if class_match:
            node_namespace = class_match.group(1)
            if node_namespace in namespaces:
                initial_nodes_to_keep.add(node_name)

    # 2. Exclure les nœuds correspondant aux mots-clés
    final_nodes_to_keep = set()
    for node_name in initial_nodes_to_keep:
        if any(keyword.lower() in node_name.lower() for keyword in keywords):
            continue  # Exclure ce nœud
        final_nodes_to_keep.add(node_name)

    # 3. Reconstruire le graphe
    filtered_node_definitions = [node_definitions[name] for name in sorted(final_nodes_to_keep) if name in node_definitions]

    filtered_edge_definitions = []
    edge_pattern = re.compile(r'"([^"]+)"\s*->\s*"([^"]+)"')
    for line in edge_lines:
        match = edge_pattern.search(line)
        if not match: continue
        source, target = match.groups()
        if source in final_nodes_to_keep and target in final_nodes_to_keep:
            filtered_edge_definitions.append(line)

    return "\n".join(header_lines + filtered_node_definitions + filtered_edge_definitions + ["}"])


def create_app(config) -> Flask:
    """Crée et configure l'application Flask (Application Factory)."""
    web_dir = Path(__file__).parent.parent / 'web'
    app = Flask(__name__,
                template_folder=str(web_dir / 'templates'),
                static_folder=str(web_dir / 'static'))

    with app.app_context():
        initialize_storage(config)

    @app.route('/api/graph', methods=['POST'])
    def api_store_graph():
        storage = get_storage()
        data = request.get_json()
        if not all(k in data for k in ['graph_type', 'dot_content']):
            return jsonify({'error': 'Missing required fields'}), 400

        graph_data = GraphData(
            graph_type=data['graph_type'],
            dot_content=data['dot_content'],
            svg_content=data.get('svg_content'),
            namespaces=set(data.get('namespaces', [])),
            stats=data.get('stats', {})
        )
        storage.store(graph_data)
        return jsonify({'status': 'success'}), 201

    @app.route('/api/graph/status', methods=['GET'])
    def api_graph_status():
        return jsonify(get_storage().get_status())

    @app.route('/api/graph/<graph_type>', methods=['GET'])
    def api_get_graph(graph_type):
        graph_data = get_storage().get(graph_type)
        if not graph_data:
            return jsonify({'error': 'Graph not found'}), 404
        return Response(graph_data.dot_content, mimetype='text/plain')

    # ... (les autres routes API de gestion de cache restent les mêmes)

    @app.route('/api/graph/filtered/<graph_type>', methods=['POST'])
    def api_get_filtered_graph(graph_type):
        storage = get_storage()
        original_graph = storage.get(graph_type)
        if not original_graph:
            return jsonify({'error': f'Graph "{graph_type}" not found in cache'}), 404

        filters = request.get_json()
        namespaces = filters.get('namespaces', [])
        keywords = filters.get('keywords', [])

        filtered_dot = _filter_dot_content(original_graph.dot_content, namespaces, keywords)
        svg_content = _convert_dot_to_svg(filtered_dot, f"{graph_type}_filtered")

        if svg_content:
            return Response(svg_content, mimetype='image/svg+xml')
        else:
            error_svg = '''<svg ...>SVG Conversion Failed...</svg>'''
            return Response(error_svg, mimetype='image/svg+xml'), 500

    @app.route('/')
    def index():
        storage = get_storage()
        status = storage.get_status()
        namespaces = set()
        stats = {'events': 0, 'agents': 0, 'connections': 0}

        if status['total_graphs'] > 0:
            for graph_info in status['graphs'].values():
                stats['events'] = max(stats['events'], graph_info.get('stats', {}).get('events', 0))
                stats['agents'] = max(stats['agents'], graph_info.get('stats', {}).get('agents', 0))
                stats['connections'] = max(stats['connections'], graph_info.get('stats', {}).get('connections', 0))
                namespaces.update(graph_info.get('namespaces', []))

        return render_template(
            'event_flow.html',
            total_events=stats['events'],
            total_agents=stats['agents'],
            total_connections=stats['connections'],
            total_namespaces=len(namespaces),
            namespaces=sorted(list(namespaces)),
            namespace_colors={},
            cache_empty=(status['total_graphs'] == 0)
        )

    # La route /graph/<graph_type> devient obsolète pour l'affichage mais on la garde comme fallback
    @app.route('/graph/<graph_type>')
    def graph(graph_type):
        storage = get_storage()
        cached_graph = storage.get(graph_type)
        if not cached_graph:
            return Response(f"Graph '{graph_type}' not found.", status=404, mimetype='image/svg+xml')

        svg_content = cached_graph.svg_content or _convert_dot_to_svg(cached_graph.dot_content, graph_type)
        if svg_content:
            return Response(svg_content, mimetype='image/svg+xml')
        else:
            return Response("SVG Conversion Failed.", status=500, mimetype='image/svg+xml')

    return app

def main():
    # ... (la fonction main reste identique) ...
    pass

if __name__ == '__main__':
    main()