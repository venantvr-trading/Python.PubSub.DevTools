#!/usr/bin/env python3
"""
Event Flow Visualization Server

Launches a web server that displays event flow diagrams in real-time with a modern UI.

Usage:
    python tools/serve_event_flow.py
    make docs-serve
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from flask import Flask, render_template, request, jsonify, Response

# Configure Flask to find templates and static files in web directory
WEB_DIR = Path(__file__).parent.parent / 'web'
app = Flask(__name__,
            template_folder=str(WEB_DIR / 'templates'),
            static_folder=str(WEB_DIR / 'static'))

# Import storage after app creation
from .storage import get_storage, GraphData

# Namespace colors (used for UI display)
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


def get_namespace_color(namespace: str) -> str:
    """Get color for a namespace"""
    return NAMESPACE_COLORS.get(namespace, NAMESPACE_COLORS['unknown'])


def _convert_dot_to_svg(dot_content: str, graph_type: str) -> bytes:
    """
    Convert DOT content to SVG using Graphviz

    Args:
        dot_content: DOT graph content as string
        graph_type: Type of graph (for error messages)

    Returns:
        SVG content as bytes, or None if conversion fails
    """
    import tempfile

    temp_dir = Path(tempfile.gettempdir())
    dot_file = temp_dir / f"cached_{graph_type}.dot"
    svg_file = temp_dir / f"cached_{graph_type}.svg"

    try:
        # Write DOT to temp file
        dot_file.write_text(dot_content)

        # Convert to SVG
        result = subprocess.run(
            ['dot', '-Tsvg', str(dot_file), '-o', str(svg_file)],
            check=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Read SVG
        svg_content = svg_file.read_bytes()
        return svg_content

    except subprocess.CalledProcessError as e:
        print(f"Error converting DOT to SVG: {e.stderr}")
        return None
    except subprocess.TimeoutExpired:
        print(f"Timeout converting DOT to SVG")
        return None
    except Exception as e:
        print(f"Unexpected error converting DOT to SVG: {e}")
        return None
    finally:
        # Cleanup
        if dot_file.exists():
            dot_file.unlink()
        if svg_file.exists():
            svg_file.unlink()


@app.route('/api/graph', methods=['POST'])
def api_store_graph():
    """
    API endpoint to receive and store graph data from scanner

    Expected JSON payload:
    {
        "graph_type": "complete|full-tree",
        "dot_content": "digraph {...}",
        "svg_content": "<svg>...</svg>",  // optional
        "namespaces": ["market_data", "position"],  // optional
        "stats": {"events": 10, "agents": 5}  // optional
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON payload provided'}), 400

        # Validate required fields
        if 'graph_type' not in data:
            return jsonify({'error': 'Missing required field: graph_type'}), 400

        if 'dot_content' not in data:
            return jsonify({'error': 'Missing required field: dot_content'}), 400

        # Valid graph types
        valid_types = {'complete', 'full-tree'}
        if data['graph_type'] not in valid_types:
            return jsonify({
                'error': f'Invalid graph_type. Must be one of: {", ".join(valid_types)}'
            }), 400

        # Convert namespaces list to set if provided
        namespaces = None
        if 'namespaces' in data and data['namespaces']:
            namespaces = set(data['namespaces'])

        # Create GraphData object
        graph_data = GraphData(
            graph_type=data['graph_type'],
            dot_content=data['dot_content'],
            svg_content=data.get('svg_content'),
            namespaces=namespaces,
            stats=data.get('stats')
        )

        # Store in cache
        storage = get_storage()
        storage.store(graph_data)

        return jsonify({
            'status': 'success',
            'graph_type': data['graph_type'],
            'timestamp': graph_data.timestamp
        }), 201

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/graph/status', methods=['GET'])
def api_graph_status():
    """Get cache status"""
    try:
        storage = get_storage()
        status = storage.get_status()
        return jsonify(status), 200
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/graph/<graph_type>', methods=['GET'])
def api_get_graph(graph_type):
    """
    Retrieve graph data from cache

    Query parameters:
    - format: dot|svg (default: dot)
    """
    try:
        storage = get_storage()
        graph_data = storage.get(graph_type)

        if not graph_data:
            return jsonify({'error': f'Graph type "{graph_type}" not found in cache'}), 404

        # Determine format
        format_type = request.args.get('format', 'dot')

        if format_type == 'svg':
            if not graph_data.svg_content:
                return jsonify({'error': 'SVG content not available for this graph'}), 404
            return Response(graph_data.svg_content, mimetype='image/svg+xml')

        elif format_type == 'dot':
            return Response(graph_data.dot_content, mimetype='text/plain')

        elif format_type == 'json':
            # Return full metadata
            return jsonify(graph_data.to_dict()), 200

        else:
            return jsonify({'error': f'Invalid format: {format_type}. Use dot, svg, or json'}), 400

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/graph/<graph_type>', methods=['DELETE'])
def api_delete_graph(graph_type):
    """Clear specific graph from cache"""
    try:
        storage = get_storage()

        if not storage.has_graph(graph_type):
            return jsonify({'error': f'Graph type "{graph_type}" not found in cache'}), 404

        storage.clear(graph_type)

        return jsonify({
            'status': 'success',
            'message': f'Graph "{graph_type}" cleared from cache'
        }), 200

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/graph', methods=['DELETE'])
def api_clear_all_graphs():
    """Clear all graphs from cache"""
    try:
        storage = get_storage()
        storage.clear()

        return jsonify({
            'status': 'success',
            'message': 'All graphs cleared from cache'
        }), 200

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/')
def index():
    """
    Main page with tabs and filters

    Gets stats from cache (populated by scanner).
    If cache is empty, shows a message to run the scanner.
    """
    storage = get_storage()
    status = storage.get_status()

    # Aggregate stats from all cached graphs
    total_events = 0
    total_agents = 0
    total_connections = 0
    namespaces = set()

    if status['total_graphs'] > 0:
        # Get stats from any cached graph (they should all have similar overall stats)
        for graph_type, graph_info in status['graphs'].items():
            if graph_info.get('stats'):
                stats = graph_info['stats']
                total_events = max(total_events, stats.get('events', 0))
                total_agents = max(total_agents, stats.get('agents', 0))
                total_connections = max(total_connections, stats.get('connections', 0))

        # Get namespaces from cached graphs
        for graph_type in status['graphs']:
            cached_graph = storage.get(graph_type)
            if cached_graph and cached_graph.namespaces:
                namespaces.update(cached_graph.namespaces)

    namespaces = sorted(namespaces) if namespaces else []
    total_namespaces = len(namespaces)

    return render_template(
        'event_flow.html',
        total_events=total_events,
        total_agents=total_agents,
        total_connections=total_connections,
        total_namespaces=total_namespaces,
        namespaces=namespaces,
        namespace_colors=NAMESPACE_COLORS,
        cache_empty=(status['total_graphs'] == 0)
    )


@app.route('/graph/<graph_type>')
def graph(graph_type):
    """
    Serve graph SVG from cache only

    The scanner is responsible for generating and pushing graphs.
    This endpoint only serves what's in the cache.
    """
    storage = get_storage()
    cached_graph = storage.get(graph_type)

    if not cached_graph:
        # Cache miss - return error SVG
        print(f"[CACHE MISS] Graph '{graph_type}' not found in cache")
        error_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400">
    <rect width="800" height="400" fill="#f5f5f5"/>
    <text x="400" y="150" font-family="Arial" font-size="18" fill="#d32f2f" text-anchor="middle" font-weight="bold">
        Graph Not Available
    </text>
    <text x="400" y="190" font-family="Arial" font-size="14" fill="#666" text-anchor="middle">
        The '{graph_type}' graph has not been generated yet.
    </text>
    <text x="400" y="220" font-family="Arial" font-size="14" fill="#666" text-anchor="middle">
        Please run the scanner to generate graphs:
    </text>
    <text x="400" y="260" font-family="Courier" font-size="12" fill="#1976d2" text-anchor="middle">
        python -m python_pubsub_devtools.event_flow.scanner --agents-dir &lt;path&gt; --one-shot
    </text>
</svg>'''
        return Response(error_svg, mimetype='image/svg+xml'), 404

    print(f"[CACHE HIT] Serving '{graph_type}' from cache")

    # If SVG is cached, return it directly
    if cached_graph.svg_content:
        return Response(cached_graph.svg_content, mimetype='image/svg+xml')

    # Otherwise, convert DOT to SVG on the fly
    print(f"[CACHE] Converting cached DOT to SVG for '{graph_type}'")
    svg_content = _convert_dot_to_svg(cached_graph.dot_content, graph_type)

    if svg_content:
        return Response(svg_content, mimetype='image/svg+xml')
    else:
        # Conversion failed - return error SVG
        error_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400">
    <rect width="800" height="400" fill="#f5f5f5"/>
    <text x="400" y="180" font-family="Arial" font-size="18" fill="#d32f2f" text-anchor="middle" font-weight="bold">
        SVG Conversion Failed
    </text>
    <text x="400" y="220" font-family="Arial" font-size="14" fill="#666" text-anchor="middle">
        Graphviz is not installed or encountered an error.
    </text>
    <text x="400" y="250" font-family="Arial" font-size="14" fill="#666" text-anchor="middle">
        Install Graphviz: sudo apt-get install graphviz
    </text>
</svg>'''
        return Response(error_svg, mimetype='image/svg+xml'), 500


def main():
    """
    Start the Event Flow API server

    The server serves graphs from cache only. Use the scanner to populate the cache:
    python -m python_pubsub_devtools.event_flow.scanner --agents-dir <path> --one-shot
    """
    import argparse
    import shutil

    parser = argparse.ArgumentParser(
        description="Event Flow Visualization API Server (cache-based)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5555,
        help="Port to run server on (default: 5555)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    args = parser.parse_args()

    print("=" * 80)
    print("🚀 Event Flow Visualization API Server")
    print("=" * 80)
    print()
    print("This server serves graphs from cache only.")
    print("Run the scanner to populate the cache:")
    print()
    print("  python -m python_pubsub_devtools.event_flow.scanner \\")
    print("    --agents-dir <path> \\")
    print("    --api-url http://localhost:5555 \\")
    print("    --one-shot")
    print()
    print("=" * 80)
    print()

    # Check Graphviz (needed for DOT→SVG conversion)
    if not shutil.which('dot'):
        print("⚠️  WARNING: Graphviz not installed!")
        print("   SVG conversion from cached DOT will fail.")
        print()
        print("   Install with:")
        print("     sudo apt-get install graphviz")
        print("     brew install graphviz  (macOS)")
        print()

    # Check cache status
    storage = get_storage()
    status = storage.get_status()

    if status['total_graphs'] > 0:
        print(f"📊 Cache status: {status['total_graphs']} graph(s) cached")
        for graph_type in status['graphs']:
            print(f"   - {graph_type}")
    else:
        print("📊 Cache status: Empty (run scanner to populate)")

    print()
    print("🌐 Starting web server...")
    print(f"   📍 API: http://{args.host}:{args.port}")
    print(f"   📍 Web UI: http://{args.host}:{args.port}")
    print()
    print("   Press Ctrl+C to stop")
    print("=" * 80)
    print()

    app.run(host=args.host, port=args.port, debug=True)


if __name__ == '__main__':
    main()