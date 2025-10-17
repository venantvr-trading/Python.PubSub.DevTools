"""
Moteur de simulation pour le Mock Exchange.

Gère la génération de scénarios de marché et le replay de données historiques.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ScenarioBasedMockExchange:
    """
    Simule un exchange basé sur des scénarios algorithmiques ou des fichiers de replay.
    """

    def __init__(self, replay_data_dir: Path | None = None):
        self.replay_data_dir = replay_data_dir
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
            return False

        logger.info(f"DEMANDE DE REPLAY: Démarrage de la simulation depuis le fichier '{filename}'.")
        # TODO: Implémenter la logique de lecture du fichier et de publication des événements.
        return True
