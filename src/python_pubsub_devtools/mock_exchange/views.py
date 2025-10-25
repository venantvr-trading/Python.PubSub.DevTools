"""
Routes Flask pour le tableau de bord Mock Exchange.

Gère l'interface web, la simulation de marché et l'API pour l'upload
de fichiers de replay de chandeliers.
"""
from __future__ import annotations

import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from flask import Flask, render_template, jsonify, request, current_app
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'csv', 'json'}


def _allowed_file(filename: str) -> bool:
    """Vérifie si l'extension du fichier est autorisée."""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_replay_files() -> List[Dict[str, Any]]:
    """Liste tous les fichiers de replay disponibles avec leurs métadonnées."""
    replay_dir = current_app.config.get('REPLAY_DATA_DIR')
    if not replay_dir or not replay_dir.exists():
        return []

    files_metadata = []
    for file_path in replay_dir.iterdir():
        if file_path.is_file() and _allowed_file(file_path.name):
            try:
                stat = file_path.stat()
                # Format timestamp as readable date
                created_dt = datetime.fromtimestamp(stat.st_mtime)
                created_at_str = created_dt.strftime('%Y-%m-%d %H:%M:%S')

                files_metadata.append({
                    'filename': file_path.name,
                    'size_kb': round(stat.st_size / 1024, 2),
                    'created_at': created_at_str,
                })
            except OSError as e:
                current_app.logger.error(f"Impossible de lire les métadonnées de {file_path}: {e}")

    # Trier par date de création, le plus récent en premier
    files_metadata.sort(key=lambda x: x['created_at'], reverse=True)
    return files_metadata


def register_routes(app: Flask) -> None:
    """Enregistre toutes les routes Flask pour le service Mock Exchange."""

    @app.route('/')
    def index():
        """Affiche le tableau de bord principal du Mock Exchange."""
        # TODO: Ajouter la logique pour les scénarios générés
        return render_template(
            'mock_exchange.html',
            title='🎰 Mock Exchange Dashboard',
            subtitle='Simulez des scénarios de marché ou rejouez des données historiques.',
            active_page='exchange',
            footer_text='🎰 Mock Exchange Dashboard | Port 5557 | <kbd>Ctrl+R</kbd> to refresh',
            replay_files=get_replay_files()
        )

    @app.route('/api/replay/files', methods=['GET'])
    def api_get_replay_files():
        """Endpoint API pour lister les fichiers de replay disponibles."""
        return jsonify(get_replay_files())

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

        # Sécuriser le nom de fichier pour éviter les traversées de répertoire
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
        mode = data.get('mode', 'pull')
        interval_seconds = data.get('interval_seconds', 1.0)

        engine = current_app.config.get('EXCHANGE_ENGINE')

        if not engine:
            return jsonify({'error': 'Le moteur de simulation n\'est pas disponible.'}), 500

        success = engine.start_replay_from_file(filename, mode=mode, interval_seconds=interval_seconds)

        if success:
            status = engine.get_replay_status()
            return jsonify({
                'success': True,
                'message': f'Replay du fichier "{filename}" démarré.',
                'total_candles': status['total_candles']
            })
        else:
            return jsonify({'error': f'Impossible de démarrer le replay pour "{filename}".'}), 500

    @app.route('/api/replay/stop', methods=['POST'])
    def api_stop_replay():
        """Endpoint API pour arrêter le replay en cours."""
        engine = current_app.config.get('EXCHANGE_ENGINE')

        if not engine:
            return jsonify({'error': 'Le moteur de simulation n\'est pas disponible.'}), 500

        success = engine.stop_replay()

        if success:
            return jsonify({'success': True, 'message': 'Replay arrêté.'})
        else:
            return jsonify({'error': 'Aucun replay en cours.'}), 400

    @app.route('/api/replay/status', methods=['GET'])
    def api_replay_status():
        """Endpoint API pour obtenir le statut du replay en cours."""
        engine = current_app.config.get('EXCHANGE_ENGINE')

        if not engine:
            return jsonify({'error': 'Le moteur de simulation n\'est pas disponible.'}), 500

        status = engine.get_replay_status()

        # Format attendu par le frontend
        return jsonify({
            'active': status['status'] == 'running',
            'session': {
                'mode': status.get('mode', 'pull'),
                'filename': status['current_file']
            },
            'cursor': status['current_index'],
            'total_candles': status['total_candles']
        })

    @app.route('/api/replay/candles', methods=['GET'])
    def api_replay_candles():
        """Endpoint API pour obtenir les candles chargées."""
        engine = current_app.config.get('EXCHANGE_ENGINE')

        if not engine:
            return jsonify({'error': 'Le moteur de simulation n\'est pas disponible.'}), 500

        candles = engine.get_candles()
        return jsonify({
            'success': True,
            'candles': candles,
            'count': len(candles)
        })

    @app.route('/api/replay/logs', methods=['GET'])
    def api_replay_logs():
        """Endpoint API pour obtenir les logs du replay."""
        engine = current_app.config.get('EXCHANGE_ENGINE')

        if not engine:
            return jsonify({'error': 'Le moteur de simulation n\'est pas disponible.'}), 500

        limit = request.args.get('limit', 100, type=int)
        logs = engine.get_logs(limit=limit)
        return jsonify({
            'success': True,
            'logs': logs
        })
