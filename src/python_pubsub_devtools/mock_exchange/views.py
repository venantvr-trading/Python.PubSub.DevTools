"""
Routes Flask pour le tableau de bord Mock Exchange.
"""
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from flask import Flask, render_template, request, jsonify, current_app

# Import du moteur de simulation
sys.path.insert(0, str(Path(__file__).parent))
from scenario_exchange import ScenarioBasedMockExchange, MarketScenario

# État global des simulations
simulations: Dict[str, Dict[str, Any]] = {}
simulation_lock = threading.Lock()


def simulation_thread(sim_id: str, config: Dict[str, Any]) -> None:
    """Thread d'exécution d'une simulation en arrière-plan.

    Args:
        sim_id: Identifiant unique de la simulation
        config: Configuration de la simulation (scénario, prix, volatilité, etc.)
    """
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

        # Récupérer le prix suivant
        exchange.fetch_current_price()
        time.sleep(0.5)  # Mise à jour toutes les 500ms

    with simulation_lock:
        simulations[sim_id]['stopped'] = True


def register_routes(app: Flask) -> None:
    """Enregistre toutes les routes Flask dans l'application.

    Args:
        app: Instance Flask
    """

    @app.route('/')
    def index():
        """Page principale du simulateur."""
        return render_template('mock_exchange.html')

    @app.route('/api/start', methods=['POST'])
    def api_start():
        """Démarre une nouvelle simulation.

        Request JSON:
            scenario: Type de scénario (ex: "uptrend", "downtrend", "sideways")
            initial_price: Prix initial
            volatility_multiplier: Multiplicateur de volatilité
            spread_bps: Spread en points de base

        Returns:
            JSON avec l'ID de la simulation créée
        """
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

        # Démarrer le thread de simulation
        thread = threading.Thread(
            target=simulation_thread,
            args=(sim_id, config),
            daemon=True
        )
        thread.start()

        return jsonify({'simulation_id': sim_id})

    @app.route('/api/pause/<sim_id>', methods=['POST'])
    def api_pause(sim_id: str):
        """Met en pause une simulation active.

        Args:
            sim_id: Identifiant de la simulation

        Returns:
            JSON avec le statut
        """
        global simulations

        with simulation_lock:
            if sim_id in simulations:
                simulations[sim_id]['running'] = False

        return jsonify({'status': 'paused'})

    @app.route('/api/stop/<sim_id>', methods=['POST'])
    def api_stop(sim_id: str):
        """Arrête une simulation active.

        Args:
            sim_id: Identifiant de la simulation

        Returns:
            JSON avec le statut
        """
        global simulations

        with simulation_lock:
            if sim_id in simulations:
                simulations[sim_id]['running'] = False
                # Gardé brièvement pour les dernières requêtes de stats

        return jsonify({'status': 'stopped'})

    @app.route('/api/stats/<sim_id>')
    def api_stats(sim_id: str):
        """Récupère les statistiques courantes d'une simulation.

        Args:
            sim_id: Identifiant de la simulation

        Returns:
            JSON avec les statistiques (prix, volatilité, retours, etc.)
        """
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
