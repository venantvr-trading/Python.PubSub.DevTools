"""
Mock Exchange Server - Flask application wrapper for Mock Exchange simulator.

Manages web interface, market simulation, and API for candlestick replay files.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any, List

from flask import Flask, render_template, jsonify, request, current_app
from werkzeug.utils import secure_filename

# Configure Flask to find templates and static files in web directory
WEB_DIR = Path(__file__).parent.parent / 'web'

ALLOWED_EXTENSIONS = {'csv', 'json'}


def _allowed_file(filename: str) -> bool:
    """Vérifie si l'extension du fichier est autorisée."""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _get_replay_files() -> List[Dict[str, Any]]:
    """Liste tous les fichiers de replay disponibles avec leurs métadonnées."""
    replay_dir = current_app.config.get('REPLAY_DATA_DIR')
    if not replay_dir or not replay_dir.exists():
        return []

    files_metadata = []
    for file_path in replay_dir.iterdir():
        if file_path.is_file() and _allowed_file(file_path.name):
            try:
                stat = file_path.stat()
                files_metadata.append({
                    'filename': file_path.name,
                    'size_kb': round(stat.st_size / 1024, 2),
                    'created_at': stat.st_mtime,
                })
            except OSError as e:
                current_app.logger.error(f"Impossible de lire les métadonnées de {file_path}: {e}")

    files_metadata.sort(key=lambda x: x['created_at'], reverse=True)
    return files_metadata


def _create_app(config) -> Flask:
    """
    Crée et configure l'application Flask pour Mock Exchange.

    Args:
        config: MockExchangeConfig avec replay_data_dir et autres paramètres

    Returns:
        Flask app configurée
    """
    app = Flask(__name__,
                template_folder=str(WEB_DIR / 'templates'),
                static_folder=str(WEB_DIR / 'static'))

    # Configuration
    replay_data_dir = Path(config.replay_data_dir) if hasattr(config, 'replay_data_dir') else None
    app.config['REPLAY_DATA_DIR'] = replay_data_dir

    # Initialiser le moteur de simulation
    from .scenario_exchange import ScenarioBasedMockExchange

    engine = ScenarioBasedMockExchange(replay_data_dir=replay_data_dir)
    app.config['EXCHANGE_ENGINE'] = engine

    # Routes
    @app.route('/')
    def index():
        """Affiche le tableau de bord principal du Mock Exchange."""
        return render_template('mock_exchange.html', replay_files=_get_replay_files())

    @app.route('/api/replay/files', methods=['GET'])
    def api_get_replay_files():
        """Endpoint API pour lister les fichiers de replay disponibles."""
        return jsonify(_get_replay_files())

    @app.route('/api/replay/upload', methods=['POST'])
    def api_upload_replay_file():
        """Endpoint API pour uploader un fichier de replay (CSV ou JSON)."""
        replay_dir = current_app.config.get('REPLAY_DATA_DIR')
        if not replay_dir:
            return jsonify({'error': 'Le répertoire de replay n\'est pas configuré.'}), 500

        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier n\'a été envoyé.'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Le nom du fichier est vide.'}), 400

        if file and _allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = Path(replay_dir) / filename

            if save_path.exists():
                return jsonify({'error': f'Le fichier "{filename}" existe déjà.'}), 409

            try:
                file.save(save_path)
                return jsonify({
                    'success': True,
                    'message': f'Fichier "{filename}" uploadé avec succès.',
                    'filename': filename
                }), 201
            except Exception as e:
                return jsonify({'error': f'Erreur lors de la sauvegarde du fichier: {e}'}), 500

        return jsonify({'error': 'Type de fichier non autorisé.'}), 400

    @app.route('/api/replay/files/<path:filename>', methods=['DELETE'])
    def api_delete_replay_file(filename: str):
        """Endpoint API pour supprimer un fichier de replay."""
        replay_dir = current_app.config.get('REPLAY_DATA_DIR')
        if not replay_dir:
            return jsonify({'error': 'Le répertoire de replay n\'est pas configuré.'}), 500

        safe_filename = secure_filename(filename)
        if safe_filename != filename:
            return jsonify({'error': 'Nom de fichier invalide.'}), 400

        file_path = Path(replay_dir) / safe_filename

        if not file_path.exists():
            return jsonify({'error': 'Fichier non trouvé.'}), 404

        try:
            os.remove(file_path)
            return jsonify({'success': True, 'message': f'Fichier "{filename}" supprimé.'})
        except OSError as e:
            return jsonify({'error': f'Erreur lors de la suppression du fichier: {e}'}), 500

    @app.route('/api/replay/start', methods=['POST'])
    def api_start_replay():
        """Endpoint API pour démarrer un replay depuis un fichier."""
        data = request.get_json()
        if not data or 'filename' not in data:
            return jsonify({'error': 'Le nom du fichier est manquant.'}), 400

        filename = secure_filename(data['filename'])
        engine = current_app.config.get('EXCHANGE_ENGINE')

        if not engine:
            return jsonify({'error': 'Le moteur de simulation n\'est pas disponible.'}), 500

        success = engine.start_replay_from_file(filename)

        if success:
            return jsonify({'success': True, 'message': f'Replay du fichier "{filename}" démarré.'})
        else:
            return jsonify({'error': f'Impossible de démarrer le replay pour "{filename}".'}), 500

    return app


class MockExchangeServer:
    """Server for Mock Exchange Simulator"""

    def __init__(self, config):
        """
        Initialise le serveur avec la configuration.

        Args:
            config: MockExchangeConfig object avec replay_data_dir et port
        """
        self.config = config
        self.port = config.port
        self.replay_data_dir = getattr(config, 'replay_data_dir', None)

        # Créer l'application Flask
        self.app = _create_app(config)

    def run(self, host: str = '0.0.0.0', debug: bool = False) -> None:
        """
        Lance le serveur Flask.

        Args:
            host: Adresse d'écoute (default: 0.0.0.0)
            debug: Active le mode debug (default: False)
        """
        print("=" * 80)
        print("🎰 Mock Exchange Simulator Server")
        print("=" * 80)
        print()
        if self.replay_data_dir:
            print(f"📂 Replay data directory: {self.replay_data_dir}")
        print()
        print(f"🌐 Server running at: http://{host}:{self.port}")
        print()
        print("   Press Ctrl+C to stop")
        print("=" * 80)
        print()

        self.app.run(host=host, port=self.port, debug=debug)
