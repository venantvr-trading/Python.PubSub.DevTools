#!/usr/bin/env python3
"""
Mock Exchange Simulator Dashboard

Web interface for running and visualizing market scenarios in real-time.

Usage:
    python tools/mock_exchange/serve_exchange.py
"""
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from flask import Flask, render_template, request, jsonify

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from scenario_exchange import ScenarioBasedMockExchange, MarketScenario

# Configure Flask to find templates and static files in parent tools directory
TOOLS_DIR = Path(__file__).parent.parent
app = Flask(__name__,
            template_folder=str(TOOLS_DIR / 'templates'),
            static_folder=str(TOOLS_DIR / 'static'))

# Paths
SCRIPT_DIR = Path(__file__).parent

# Global simulation state
simulations: Dict[str, Dict[str, Any]] = {}
simulation_lock = threading.Lock()


def simulation_thread(sim_id: str, config: Dict[str, Any]):
    """Background thread to run simulation"""
    global simulations

    exchange = ScenarioBasedMockExchange(
        scenario=MarketScenario(config['scenario']),
        initial_price=config['initial_price'],
        volatility_multiplier=config['volatility_multiplier'],
        spread_bps=config['spread_bps']
    )

    with simulation_lock:
        simulations[sim_id]['exchange'] = exchange
        simulations[sim_id]['running'] = True

    while True:
        with simulation_lock:
            if not simulations[sim_id]['running']:
                break

        # Fetch next price
        exchange.fetch_current_price()
        time.sleep(0.5)  # Update every 500ms

    with simulation_lock:
        simulations[sim_id]['stopped'] = True


@app.route('/')
def index():
    """Main page"""
    return render_template('mock_exchange.html')


@app.route('/api/start', methods=['POST'])
def api_start():
    """Start a new simulation"""
    global simulations

    config = request.json
    sim_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    with simulation_lock:
        simulations[sim_id] = {
            'config': config,
            'exchange': None,
            'running': False,
            'stopped': False
        }

    # Start simulation thread
    thread = threading.Thread(target=simulation_thread, args=(sim_id, config), daemon=True)
    thread.start()

    return jsonify({'simulation_id': sim_id})


@app.route('/api/pause/<sim_id>', methods=['POST'])
def api_pause(sim_id: str):
    """Pause simulation"""
    global simulations

    with simulation_lock:
        if sim_id in simulations:
            simulations[sim_id]['running'] = False

    return jsonify({'status': 'paused'})


@app.route('/api/stop/<sim_id>', methods=['POST'])
def api_stop(sim_id: str):
    """Stop simulation"""
    global simulations

    with simulation_lock:
        if sim_id in simulations:
            simulations[sim_id]['running'] = False
            # Remove from active simulations after a delay
            # (keep it briefly for final stats request)

    return jsonify({'status': 'stopped'})


@app.route('/api/stats/<sim_id>')
def api_stats(sim_id: str):
    """Get current simulation statistics"""
    global simulations

    with simulation_lock:
        if sim_id not in simulations:
            return jsonify({'error': 'Simulation not found'}), 404

        sim = simulations[sim_id]
        exchange = sim.get('exchange')

        if not exchange:
            return jsonify({'running': False})

        stats = exchange.get_price_statistics()

        return jsonify({
            'running': sim['running'],
            'current_price': exchange.current_price,
            'total_return_pct': stats['total_return_pct'],
            'min_price': stats['min_price'],
            'max_price': stats['max_price'],
            'volatility': stats['volatility'],
            'call_count': stats['call_count']
        })


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Mock Exchange Simulator Dashboard")
    parser.add_argument("--port", type=int, default=5557, help="Port to run server on (default: 5557)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    args = parser.parse_args()

    print("=" * 80)
    print("🎰 Mock Exchange Simulator Dashboard")
    print("=" * 80)
    print()
    print("🌐 Starting web server...")
    print()
    print(f"   📍 Open in browser: http://{args.host}:{args.port}")
    print()
    print("   Press Ctrl+C to stop")
    print("=" * 80)
    print()

    app.run(host=args.host, port=args.port, debug=False, threaded=True)


if __name__ == '__main__':
    main()
