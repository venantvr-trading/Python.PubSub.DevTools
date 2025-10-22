"""
Moteur de simulation pour le Mock Exchange.

Gère la génération de scénarios de marché et le replay de données historiques.
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ScenarioBasedMockExchange:
    """
    Simule un exchange basé sur des scénarios algorithmiques ou des fichiers de replay.

    Args:
        replay_data_dir: Répertoire contenant les fichiers de replay (CSV, JSON)
        service_bus: Instance du ServiceBus pour publier les événements de marché
    """

    def __init__(self, replay_data_dir: Path | None = None, service_bus: Any | None = None):
        """
        Initialise le moteur de simulation.

        Args:
            replay_data_dir: Répertoire des fichiers de replay
            service_bus: Bus d'événements pour publier les données de marché
        """
        self.replay_data_dir = replay_data_dir
        self.service_bus = service_bus

        # État du replay
        self._replay_state_lock = threading.Lock()
        self._current_file: Optional[str] = None
        self._replay_status: str = "stopped"  # stopped, running, paused, completed
        self._candles: List[Dict[str, Any]] = []
        self._logs: List[Dict[str, Any]] = []
        self._current_index: int = 0
        self._replay_thread: Optional[threading.Thread] = None

        logger.info("ScenarioBasedMockExchange initialisé.")

    def start_replay_from_file(self, filename: str) -> bool:
        """
        Démarre une simulation en lisant les données d'un fichier de replay.

        Args:
            filename: Le nom du fichier à rejouer (doit être dans replay_data_dir).

        Returns:
            True si le replay a pu être démarré, False sinon.
        """
        if not self.replay_data_dir:
            logger.error("Le répertoire de replay n'est pas configuré.")
            self._add_log("error", "Le répertoire de replay n'est pas configuré")
            return False

        file_path = Path(self.replay_data_dir) / filename
        if not file_path.exists():
            logger.error(f"Le fichier {filename} n'existe pas")
            self._add_log("error", f"Le fichier {filename} n'existe pas")
            return False

        with self._replay_state_lock:
            # Arrêter le replay précédent si nécessaire
            if self._replay_status == "running":
                logger.warning("Un replay est déjà en cours")
                return False

            # Charger le fichier
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                if 'candles' not in data:
                    logger.error("Le fichier JSON ne contient pas de tableau 'candles'")
                    self._add_log("error", "Format JSON invalide: tableau 'candles' manquant")
                    return False

                self._candles = data['candles']
                self._current_file = filename
                self._replay_status = "running"
                self._current_index = 0
                self._logs = []

                self._add_log("info", f"Replay démarré: {filename}")
                self._add_log("info", f"Total candles: {len(self._candles)}")

                logger.info(f"Replay démarré depuis '{filename}' avec {len(self._candles)} candles")
                return True

            except json.JSONDecodeError as e:
                logger.error(f"Erreur lors de la lecture du fichier JSON: {e}")
                self._add_log("error", f"Erreur JSON: {str(e)}")
                return False
            except Exception as e:
                logger.error(f"Erreur inattendue lors du chargement: {e}")
                self._add_log("error", f"Erreur: {str(e)}")
                return False

    def stop_replay(self) -> bool:
        """
        Arrête le replay en cours.

        Returns:
            True si le replay a été arrêté, False sinon.
        """
        with self._replay_state_lock:
            if self._replay_status != "running":
                return False

            self._replay_status = "stopped"
            self._add_log("info", "Replay arrêté")
            logger.info("Replay arrêté")
            return True

    def get_replay_status(self) -> Dict[str, Any]:
        """
        Retourne le statut actuel du replay.

        Returns:
            Dictionnaire avec le statut, fichier, progression, etc.
        """
        with self._replay_state_lock:
            return {
                'status': self._replay_status,
                'current_file': self._current_file,
                'total_candles': len(self._candles),
                'current_index': self._current_index,
                'progress': round((self._current_index / len(self._candles) * 100), 2) if self._candles else 0
            }

    def get_candles(self) -> List[Dict[str, Any]]:
        """
        Retourne les candles chargées.

        Returns:
            Liste des candles
        """
        with self._replay_state_lock:
            return self._candles.copy()

    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retourne les logs du replay.

        Args:
            limit: Nombre maximum de logs à retourner

        Returns:
            Liste des logs (les plus récents en premier)
        """
        with self._replay_state_lock:
            return self._logs[-limit:][::-1]  # Inverser pour avoir les plus récents en premier

    def _add_log(self, level: str, message: str) -> None:
        """
        Ajoute un log au replay (thread-safe).

        Args:
            level: Niveau du log (info, warning, error)
            message: Message du log
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),  # ISO format pour que JS puisse parser
            'level': level,
            'message': message
        }
        self._logs.append(log_entry)
