"""
Routes Flask pour le tableau de bord Scenario Testing.
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

import yaml
from flask import Flask, render_template, request, jsonify, current_app

# État global des exécutions de tests
test_runs: Dict[str, Dict[str, Any]] = {}
test_runs_lock = threading.Lock()


class ListLogHandler(logging.Handler):
    """Un handler de logging qui stocke les logs dans une liste."""

    def __init__(self, log_list: List[Dict[str, Any]]):
        super().__init__()
        self.log_list = log_list

    def emit(self, record: logging.LogRecord):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).strftime('%H:%M:%S'),
            'level': record.levelname.lower(),
            'message': self.format(record)
        }
        self.log_list.append(log_entry)


def load_scenario_metadata(filepath: Path) -> Optional[Dict[str, Any]]:
    """Charge les métadonnées d'un fichier de scénario YAML.

    Args:
        filepath: Chemin vers le fichier YAML

    Returns:
        Dictionnaire de métadonnées ou None si erreur
    """
    try:
        with open(filepath, 'r') as f:
            scenario = yaml.safe_load(f)

        return {
            'filename': filepath.name,
            'name': scenario.get('name', filepath.stem),
            'description': scenario.get('description', ''),
            'has_chaos': len(scenario.get('chaos', [])) > 0,
            'setup': scenario.get('setup', {})
        }
    except Exception as e:
        print(f"Error loading scenario {filepath}: {e}")
        return None


def load_scenario_content(filename: str) -> Optional[str]:
    """Charge le contenu brut d'un fichier de scénario.

    Args:
        filename: Nom du fichier

    Returns:
        Contenu du fichier ou None si erreur
    """
    try:
        scenarios_dir = Path(current_app.config['SCENARIOS_DIR'])
        filepath = scenarios_dir / filename
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading scenario content {filename}: {e}")
        return None


def run_test_thread(test_id: str) -> None:
    """Thread d'exécution d'un test en arrière-plan.

    Cette fonction simule l'exécution d'un test. Dans une vraie implémentation,
    elle appellerait le scenario_runner pour exécuter le scénario complet.

    Args:
        test_id: Identifiant unique du test
    """
    global test_runs

    try:
        with test_runs_lock:
            test_run = test_runs[test_id]

        # Simuler l'exécution du test avec des délais
        # TODO: Intégrer avec scenario_runner pour vraie exécution
        time.sleep(1)

        with test_runs_lock:
            test_run['log'].append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'level': 'info',
                'message': 'Loading scenario configuration...'
            })

        time.sleep(1)

        with test_runs_lock:
            test_run['log'].append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'level': 'info',
                'message': 'Setting up mock exchange...'
            })

        time.sleep(1)

        with test_runs_lock:
            test_run['log'].append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'level': 'success',
                'message': 'Test execution completed'
            })

            # Résultats mockés
            test_run['status'] = 'passed'
            test_run['duration_seconds'] = 3.5
            test_run['assertions_passed'] = 5
            test_run['assertions_total'] = 5
            test_run['events_count'] = 127
            test_run['assertions'] = [
                {'name': 'event_count.PositionPurchased.min', 'passed': True,
                 'message': 'Expected at least 3, got 5'},
                {'name': 'event_count.PositionSold.max', 'passed': True,
                 'message': 'Expected at most 2, got 1'},
                {'name': 'no_panic_sell', 'passed': True,
                 'message': 'No panic selling detected during crash'},
                {'name': 'final_capital.min', 'passed': True,
                 'message': 'Capital above minimum threshold'},
                {'name': 'event_sequence', 'passed': True,
                 'message': 'Events occurred in correct order'},
            ]
            test_run['chaos'] = {
                'events_delayed': 1,
                'events_dropped': 0,
                'failures_injected': 0,
                'total_delay_ms': 5000
            }

    except Exception as e:
        with test_runs_lock:
            test_run['status'] = 'failed'
            test_run['log'].append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'level': 'error',
                'message': f'Test failed: {str(e)}'
            })


def register_routes(app: Flask) -> None:
    """Enregistre toutes les routes Flask dans l'application.

    Args:
        app: Instance Flask
    """

    @app.route('/')
    def index():
        """Page principale du tableau de bord."""
        return render_template(
            'scenario_testing.html',
            title='🎯 Scenario Testing Dashboard',
            subtitle='Declarative testing with chaos engineering',
            active_page='testing',
            footer_text='🎯 Scenario Testing Dashboard | Port 5558 | <kbd>Ctrl+R</kbd> to refresh'
        )

    @app.route('/api/scenarios')
    def api_scenarios():
        """Liste tous les scénarios disponibles."""
        scenarios = []
        scenarios_dir = Path(current_app.config['SCENARIOS_DIR'])

        if scenarios_dir.exists():
            for filepath in scenarios_dir.glob('*.yaml'):
                metadata = load_scenario_metadata(filepath)
                if metadata:
                    scenarios.append(metadata)

        return jsonify(scenarios)

    @app.route('/api/scenario/<filename>')
    def api_scenario(filename: str):
        """Récupère les détails d'un scénario spécifique."""
        scenarios_dir = Path(current_app.config['SCENARIOS_DIR'])
        metadata = load_scenario_metadata(scenarios_dir / filename)
        if not metadata:
            return jsonify({'error': 'Scenario not found'}), 404

        content = load_scenario_content(filename)
        metadata['content'] = content

        return jsonify(metadata)

    @app.route('/api/run', methods=['POST'])
    def api_run():
        """Démarre l'exécution d'un test.

        Request JSON:
            scenario: Nom du fichier de scénario
            verbose: Mode verbeux (optionnel)
            recording: Activer l'enregistrement (optionnel)

        Returns:
            JSON avec l'ID du test créé
        """
        global test_runs

        config = request.json
        test_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        with test_runs_lock:
            test_runs[test_id] = {
                'scenario': config['scenario'],
                'verbose': config.get('verbose', False),
                'recording': config.get('recording', True),
                'status': 'running',
                'start_time': datetime.now().isoformat(),
                'log': [
                    {'timestamp': datetime.now().strftime('%H:%M:%S'),
                     'level': 'info',
                     'message': 'Test execution started'},
                    {'timestamp': datetime.now().strftime('%H:%M:%S'),
                     'level': 'info',
                     'message': f'Scenario: {config["scenario"]}'},
                ],
                'assertions': [],
                'chaos': {},
                'events_count': 0
            }

        # Démarrer le test en thread d'arrière-plan
        thread = threading.Thread(target=run_test_thread, args=(test_id,), daemon=True)
        thread.start()

        return jsonify({'test_id': test_id})

    @app.route('/api/stop/<test_id>', methods=['POST'])
    def api_stop(test_id: str):
        """Arrête un test en cours d'exécution."""
        global test_runs

        with test_runs_lock:
            if test_id in test_runs:
                test_runs[test_id]['status'] = 'stopped'
                test_runs[test_id]['log'].append({
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'level': 'warning',
                    'message': 'Test execution stopped by user'
                })

        return jsonify({'status': 'stopped'})

    @app.route('/api/status/<test_id>')
    def api_status(test_id: str):
        """Récupère le statut actuel d'un test."""
        global test_runs

        with test_runs_lock:
            if test_id not in test_runs:
                return jsonify({'error': 'Test not found'}), 404

            test_run = test_runs[test_id].copy()

        return jsonify(test_run)

    @app.route('/api/pubsub/status')
    def api_pubsub_status():
        """Récupère le statut de connexion PubSub depuis mock_exchange."""
        import requests
        try:
            response = requests.get('http://localhost:5557/api/replay/status', timeout=1)
            if response.ok:
                data = response.json()
                return jsonify({'connected': data.get('pubsub_connected', False)})
        except:
            pass
        return jsonify({'connected': False})

    # ===== Risk Analysis API Routes =====

    # Global state for risk analysis
    risk_state = {
        'data_loader': None,
        'hmm_trainer': None,
        'gan_trainers': {},  # regime_id -> GANTrainer
        'training_status': {}  # track async training
    }

    @app.route('/api/risk/upload', methods=['POST'])
    def api_risk_upload():
        """Upload and parse CSV data"""
        from python_pubsub_devtools.risk_analysis import DataLoader

        data = request.get_json()
        csv_content = data.get('csv_content')

        if not csv_content:
            return jsonify({'error': 'No CSV content provided'}), 400

        loader = DataLoader()
        result = loader.parse_csv(csv_content)

        if 'error' in result:
            return jsonify(result), 400

        # Store in state
        risk_state['data_loader'] = loader

        return jsonify(result)

    @app.route('/api/risk/train_hmm', methods=['POST'])
    def api_risk_train_hmm():
        """Train HMM for regime detection"""
        from python_pubsub_devtools.risk_analysis import HMMTrainer

        if risk_state['data_loader'] is None:
            return jsonify({'error': 'No data loaded. Upload CSV first'}), 400

        try:
            # Extract features
            features = risk_state['data_loader'].extract_features()

            # Train HMM
            trainer = HMMTrainer(n_regimes=3)
            result = trainer.train(features)

            if 'error' in result:
                return jsonify(result), 400

            # Store in state
            risk_state['hmm_trainer'] = trainer

            return jsonify(result)

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/risk/train_gan', methods=['POST'])
    def api_risk_train_gan():
        """Train GAN for specific regime"""
        from python_pubsub_devtools.risk_analysis import GANTrainer

        data = request.get_json()
        regime_id = data.get('regime_id')

        if regime_id is None:
            return jsonify({'error': 'regime_id required'}), 400

        regime_id = int(regime_id)

        if risk_state['data_loader'] is None:
            return jsonify({'error': 'No data loaded'}), 400

        if risk_state['hmm_trainer'] is None:
            return jsonify({'error': 'HMM not trained'}), 400

        try:
            # Get regime-specific candles
            candles = risk_state['data_loader'].get_candles()

            # Filter by regime (simplified - in real scenario, use HMM predictions)
            # For now, use all candles
            regime_candles = candles

            # Train GAN asynchronously
            def train_async():
                trainer = GANTrainer(regime_id=regime_id)
                result = trainer.train(regime_candles, epochs=50, batch_size=16)
                risk_state['gan_trainers'][regime_id] = trainer
                risk_state['training_status'][regime_id] = result

            # Mark as training
            risk_state['training_status'][regime_id] = {'status': 'training'}

            # Start training thread
            thread = threading.Thread(target=train_async, daemon=True)
            thread.start()

            return jsonify({
                'success': True,
                'regime_id': regime_id,
                'status': 'training_started'
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/risk/gan_status/<int:regime_id>')
    def api_risk_gan_status(regime_id):
        """Check GAN training status"""
        status = risk_state['training_status'].get(regime_id)

        if status is None:
            return jsonify({'error': 'No training found'}), 404

        return jsonify(status)

    @app.route('/api/risk/simulate', methods=['POST'])
    def api_risk_simulate():
        """Generate scenarios"""
        from python_pubsub_devtools.risk_analysis import ScenarioGenerator, ExportManager

        data = request.get_json()
        n_scenarios = data.get('n_scenarios', 100)
        n_candles = data.get('n_candles', 240)
        mode = data.get('mode', 'gbm')  # 'gbm' or 'gan'

        if risk_state['hmm_trainer'] is None:
            return jsonify({'error': 'HMM not trained'}), 400

        try:
            # Get regime parameters
            regime_stats = risk_state['hmm_trainer'].regime_stats
            regime_params = {}

            for regime_id, stats in regime_stats.items():
                regime_params[regime_id] = {
                    'drift': stats['avg_return'],
                    'volatility': stats['avg_volatility'],
                    'prob': stats['prob']
                }

            # Determine start price
            if risk_state['data_loader'] and risk_state['data_loader'].data is not None:
                start_price = float(risk_state['data_loader'].data['close'].iloc[-1])
            else:
                start_price = 35000.0

            # Generate scenarios
            generator = ScenarioGenerator(mode=mode)

            if mode == 'gan':
                generator.load_gan_models(list(regime_params.keys()))

            scenarios = generator.generate_scenarios(
                n_scenarios=n_scenarios,
                n_candles=n_candles,
                start_price=start_price,
                regime_params=regime_params,
                interval_minutes=1
            )

            # Export to files
            exporter = ExportManager()
            results = exporter.save_scenarios_batch(
                scenarios=scenarios,
                prefix='risk_scenario',
                metadata={
                    'mode': mode,
                    'start_price': start_price,
                    'n_scenarios': n_scenarios,
                    'n_candles': n_candles
                }
            )

            return jsonify({
                'success': True,
                'n_scenarios': len(results),
                'files': [r['filename'] for r in results],
                'mode': mode
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500
