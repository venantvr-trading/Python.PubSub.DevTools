"""
Moteur de simulation pour le Mock Exchange.

Gère la génération de scénarios de marché et le replay de données historiques.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class ScenarioBasedMockExchange:
    """
    Simule un exchange basé sur des scénarios algorithmiques ou des fichiers de replay.

    Args:
        replay_data_dir: Répertoire contenant les fichiers de replay (CSV, JSON)
        service_bus: Instance du ServiceBus pour publier les événements de marché
    """

    def __init__(
            self,
            replay_data_dir: Path | None = None,
            service_bus: Any | None = None,
            get_receivers_callback: Optional[Callable[[], List[Dict[str, str]]]] = None
    ):
        """
        Initialise le moteur de simulation.

        Args:
            replay_data_dir: Répertoire des fichiers de replay
            service_bus: Bus d'événements pour publier les données de marché
            get_receivers_callback: Fonction pour obtenir la liste des receivers enregistrés
        """
        self.replay_data_dir = replay_data_dir
        self.service_bus = service_bus
        self.get_receivers = get_receivers_callback or (lambda: [])

        # État du replay
        self._replay_state_lock = threading.Lock()
        self._current_file: Optional[str] = None
        self._replay_status: str = "stopped"  # stopped, running, paused, completed
        self._replay_mode: str = "pull"  # pull ou push
        self._interval_seconds: float = 1.0
        self._candles: List[Dict[str, Any]] = []
        self._logs: List[Dict[str, Any]] = []
        self._current_index: int = 0
        self._replay_thread: Optional[threading.Thread] = None
        self._stop_thread_event = threading.Event()

        logger.info("ScenarioBasedMockExchange initialisé.")

    def start_replay_from_file(
            self,
            filename: str,
            mode: str = "pull",
            interval_seconds: float = 1.0
    ) -> bool:
        """
        Démarre une simulation en lisant les données d'un fichier de replay.

        Args:
            filename: Le nom du fichier à rejouer (doit être dans replay_data_dir).
            mode: Mode de replay ("pull" ou "push")
            interval_seconds: Intervalle en secondes entre chaque chandelle en mode push

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

            # Validation du mode push
            if mode == "push":
                receivers = self.get_receivers()
                if not receivers:
                    logger.error("Mode push requiert au moins un receiver enregistré")
                    self._add_log("error", "Mode push: aucun receiver enregistré")
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
                self._replay_mode = mode
                self._interval_seconds = interval_seconds
                self._current_index = 0
                self._logs = []
                self._stop_thread_event.clear()

                self._add_log("info", f"Replay démarré: {filename} (mode: {mode})")
                self._add_log("info", f"Total candles: {len(self._candles)}")

                # Démarrer le thread de push si nécessaire
                if mode == "push":
                    self._replay_thread = threading.Thread(target=self._push_replay_loop, daemon=True)
                    self._replay_thread.start()
                    self._add_log("info", f"Thread push démarré (interval: {interval_seconds}s)")

                logger.info(f"Replay démarré depuis '{filename}' avec {len(self._candles)} candles en mode {mode}")
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
            self._stop_thread_event.set()
            self._add_log("info", "Replay arrêté")
            logger.info("Replay arrêté")

            # Attendre que le thread se termine
            if self._replay_thread and self._replay_thread.is_alive():
                # Libérer le lock pendant l'attente
                pass

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
                'mode': self._replay_mode,
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

    def _push_replay_loop(self) -> None:
        """
        Thread qui envoie les chandelles progressivement aux receivers enregistrés.
        """
        logger.info("Thread push démarré")

        while not self._stop_thread_event.is_set():
            with self._replay_state_lock:
                if self._replay_status != "running":
                    break

                if self._current_index >= len(self._candles):
                    self._replay_status = "completed"
                    self._add_log("info", "Replay terminé")
                    logger.info("Replay terminé")
                    break

                # Récupérer la chandelle courante
                candle = self._candles[self._current_index]

            # Envoyer aux receivers (hors du lock pour éviter les blocages)
            receivers = self.get_receivers()
            if not receivers:
                logger.warning("Aucun receiver disponible, arrêt du push")
                with self._replay_state_lock:
                    self._add_log("warning", "Aucun receiver disponible")
                    self._replay_status = "stopped"
                break

            # Envoyer à tous les receivers
            for receiver in receivers:
                endpoint = receiver.get('player_endpoint') or receiver.get('receiver_endpoint')
                consumer_name = receiver.get('consumer_name', 'Unknown')

                if not endpoint:
                    continue

                try:
                    response = requests.post(
                        endpoint,
                        json={'candle': candle, 'index': self._current_index},
                        timeout=2.0
                    )
                    if response.ok:
                        logger.debug(f"Chandelle {self._current_index} envoyée à {consumer_name}")
                    else:
                        logger.warning(f"Erreur HTTP {response.status_code} de {consumer_name}")
                        with self._replay_state_lock:
                            self._add_log("warning", f"{consumer_name}: HTTP {response.status_code}")
                except requests.exceptions.RequestException as e:
                    logger.error(f"Erreur d'envoi à {consumer_name}: {e}")
                    with self._replay_state_lock:
                        self._add_log("error", f"{consumer_name}: {str(e)}")

            # Incrémenter l'index et logger
            with self._replay_state_lock:
                self._current_index += 1
                if self._current_index % 10 == 0:  # Log tous les 10 candles
                    self._add_log("info", f"Progression: {self._current_index}/{len(self._candles)}")

            # Attendre l'intervalle
            time.sleep(self._interval_seconds)

        logger.info("Thread push terminé")

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
