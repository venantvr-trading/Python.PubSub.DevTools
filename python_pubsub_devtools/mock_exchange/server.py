"""
Mock Exchange Simulator Dashboard Server

Web interface for running and visualizing market scenarios.
"""
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from flask import Flask, render_template, request, jsonify

from .scenario_exchange import ScenarioBasedMockExchange, MarketScenario
from ..config import MockExchangeConfig


class MockExchangeServer:
    """Flask server for mock exchange dashboard"""

    def __init__(self, config: MockExchangeConfig):
        self.config = config
        self.simulations: Dict[str, Dict[str, Any]] = {}
        self.simulation_lock = threading.Lock()
        self.app = self._create_app()

    def _create_app(self) -> Flask:
        package_root = Path(__file__).parent.parent
        app = Flask(__name__,
                    template_folder=str(package_root / 'web' / 'templates'),
                    static_folder=str(package_root / 'web' / 'static'))

        @app.route('/')
        def index():
            return render_template('mock_exchange.html')

        @app.route('/api/start', methods=['POST'])
        def api_start():
            return self._api_start()

        @app.route('/api/pause/<sim_id>', methods=['POST'])
        def api_pause(sim_id: str):
            return self._api_pause(sim_id)

        @app.route('/api/stop/<sim_id>', methods=['POST'])
        def api_stop(sim_id: str):
            return self._api_stop(sim_id)

        @app.route('/api/stats/<sim_id>')
        def api_stats(sim_id: str):
            return self._api_stats(sim_id)

        return app

    def _simulation_thread(self, sim_id: str, config: Dict[str, Any]):
        """Background thread to run simulation"""
        exchange = ScenarioBasedMockExchange(
            scenario=MarketScenario(config['scenario']),
            initial_price=config['initial_price'],
            volatility_multiplier=config['volatility_multiplier'],
            spread_bps=config['spread_bps']
        )

        with self.simulation_lock:
            self.simulations[sim_id]['exchange'] = exchange
            self.simulations[sim_id]['running'] = True

        while True:
            with self.simulation_lock:
                if not self.simulations[sim_id]['running']:
                    break

            exchange.fetch_current_price()
            time.sleep(0.5)

        with self.simulation_lock:
            self.simulations[sim_id]['stopped'] = True

    def _api_start(self):
        config = request.json
        sim_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        with self.simulation_lock:
            self.simulations[sim_id] = {
                'config': config,
                'exchange': None,
                'running': False,
                'stopped': False
            }

        thread = threading.Thread(target=self._simulation_thread, args=(sim_id, config), daemon=True)
        thread.start()

        return jsonify({'simulation_id': sim_id})

    def _api_pause(self, sim_id: str):
        with self.simulation_lock:
            if sim_id in self.simulations:
                self.simulations[sim_id]['running'] = False
        return jsonify({'status': 'paused'})

    def _api_stop(self, sim_id: str):
        with self.simulation_lock:
            if sim_id in self.simulations:
                self.simulations[sim_id]['running'] = False
        return jsonify({'status': 'stopped'})

    def _api_stats(self, sim_id: str):
        with self.simulation_lock:
            if sim_id not in self.simulations:
                return jsonify({'error': 'Simulation not found'}), 404

            sim = self.simulations[sim_id]
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

    def run(self, host: str = '0.0.0.0', debug: bool = False):
        print("=" * 80)
        print("🎰 Mock Exchange Simulator Dashboard")
        print("=" * 80)
        print()
        print("🌐 Starting web server...")
        print(f"   📍 Open in browser: http://localhost:{self.config.port}")
        print("   Press Ctrl+C to stop")
        print("=" * 80)
        print()

        self.app.run(host=host, port=self.config.port, debug=debug, threaded=True)
        return 0
