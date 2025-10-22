"""Tests pour ScenarioBasedMockExchange - vérifie qu'on poste bien aux applications enregistrées."""
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from python_pubsub_devtools.mock_exchange.scenario_exchange import ScenarioBasedMockExchange


class TestScenarioBasedMockExchange:
    """Tests pour le moteur de simulation Mock Exchange."""

    @pytest.fixture
    def temp_replay_dir(self):
        """Crée un répertoire temporaire pour les tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_candles_file(self, temp_replay_dir):
        """Crée un fichier JSON de candles pour les tests."""
        candles_data = {
            "candles": [
                {"timestamp": "2024-01-01T00:00:00Z", "open": 50000, "close": 50100, "high": 50150, "low": 49950, "volume": 100},
                {"timestamp": "2024-01-01T00:01:00Z", "open": 50100, "close": 50200, "high": 50250, "low": 50050, "volume": 120},
                {"timestamp": "2024-01-01T00:02:00Z", "open": 50200, "close": 50150, "high": 50300, "low": 50100, "volume": 90},
            ]
        }

        filepath = temp_replay_dir / "test_candles.json"
        with open(filepath, "w") as f:
            json.dump(candles_data, f)

        return filepath.name

    def test_receiver_registration(self):
        """Vérifie qu'on peut tracker les receivers enregistrés."""
        receivers = []

        def get_receivers_callback():
            return receivers

        engine = ScenarioBasedMockExchange(
            get_receivers_callback=get_receivers_callback
        )

        # Simuler l'enregistrement de receivers
        receivers.append({
            "consumer_name": "TradingBot1",
            "player_endpoint": "http://localhost:8080/candle"
        })

        assert len(engine.get_receivers()) == 1

    @patch('python_pubsub_devtools.mock_exchange.scenario_exchange.requests.post')
    def test_push_mode_posts_to_registered_receivers(
            self, mock_post, temp_replay_dir, sample_candles_file
    ):
        """Vérifie que le mode push poste aux receivers enregistrés via HTTP POST."""
        # Setup receivers
        receivers = [
            {
                "consumer_name": "Bot1",
                "player_endpoint": "http://localhost:8080/candle"
            },
            {
                "consumer_name": "Bot2",
                "receiver_endpoint": "http://localhost:8081/candle"  # Test alias
            }
        ]

        def get_receivers():
            return receivers

        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        # Create engine
        engine = ScenarioBasedMockExchange(
            replay_data_dir=temp_replay_dir,
            get_receivers_callback=get_receivers
        )

        # Start replay in push mode
        success = engine.start_replay_from_file(
            sample_candles_file,
            mode="push",
            interval_seconds=0.01  # Très court pour le test
        )

        assert success is True

        # Attendre que quelques candles soient envoyées
        time.sleep(0.1)

        # Stop replay
        engine.stop_replay()

        # Verify that requests were made
        assert mock_post.call_count > 0

        # Vérifier qu'on a bien posté à Bot1
        bot1_calls = [
            c for c in mock_post.call_args_list
            if c[0][0] == "http://localhost:8080/candle"
        ]
        assert len(bot1_calls) > 0

        # Vérifier qu'on a bien posté à Bot2
        bot2_calls = [
            c for c in mock_post.call_args_list
            if c[0][0] == "http://localhost:8081/candle"
        ]
        assert len(bot2_calls) > 0

        # Vérifier le format des données postées
        first_call = mock_post.call_args_list[0]
        json_data = first_call[1]["json"]
        assert "candle" in json_data
        assert "index" in json_data
        assert json_data["candle"]["open"] == 50000

    @patch('python_pubsub_devtools.mock_exchange.scenario_exchange.requests.post')
    def test_push_mode_posts_all_candles_to_all_receivers(
            self, mock_post, temp_replay_dir, sample_candles_file
    ):
        """Vérifie que chaque candle est postée à tous les receivers."""
        receivers = [
            {"consumer_name": "Bot1", "player_endpoint": "http://localhost:8080/candle"},
            {"consumer_name": "Bot2", "player_endpoint": "http://localhost:8081/candle"},
        ]

        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        engine = ScenarioBasedMockExchange(
            replay_data_dir=temp_replay_dir,
            get_receivers_callback=lambda: receivers
        )

        engine.start_replay_from_file(
            sample_candles_file,
            mode="push",
            interval_seconds=0.01
        )

        # Attendre que toutes les candles soient envoyées
        time.sleep(0.15)
        engine.stop_replay()

        # On devrait avoir au moins 3 candles × 2 receivers = 6 appels
        assert mock_post.call_count >= 6

        # Vérifier que Bot1 a reçu plusieurs candles
        bot1_calls = [
            c for c in mock_post.call_args_list
            if c[0][0] == "http://localhost:8080/candle"
        ]
        assert len(bot1_calls) >= 3

        # Vérifier que Bot2 a reçu plusieurs candles
        bot2_calls = [
            c for c in mock_post.call_args_list
            if c[0][0] == "http://localhost:8081/candle"
        ]
        assert len(bot2_calls) >= 3

    @patch('python_pubsub_devtools.mock_exchange.scenario_exchange.requests.post')
    def test_push_mode_handles_receiver_failures(
            self, mock_post, temp_replay_dir, sample_candles_file
    ):
        """Vérifie qu'on gère les erreurs de receivers."""
        import requests

        receivers = [
            {
                "consumer_name": "FailingBot",
                "player_endpoint": "http://localhost:9999/candle"
            }
        ]

        # Simuler une erreur de connexion
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        engine = ScenarioBasedMockExchange(
            replay_data_dir=temp_replay_dir,
            get_receivers_callback=lambda: receivers
        )

        success = engine.start_replay_from_file(
            sample_candles_file,
            mode="push",
            interval_seconds=0.01
        )

        assert success is True

        # Attendre un peu
        time.sleep(0.05)

        # Vérifier qu'on a bien tenté d'envoyer
        assert mock_post.call_count > 0

        # Vérifier que les erreurs sont loguées
        logs = engine.get_logs()
        error_logs = [log for log in logs if log["level"] == "error"]
        assert len(error_logs) > 0

        engine.stop_replay()

    def test_push_mode_fails_without_receivers(
            self, temp_replay_dir, sample_candles_file
    ):
        """Vérifie qu'on ne peut pas démarrer en push sans receivers."""
        engine = ScenarioBasedMockExchange(
            replay_data_dir=temp_replay_dir,
            get_receivers_callback=lambda: []  # Aucun receiver
        )

        success = engine.start_replay_from_file(
            sample_candles_file,
            mode="push"
        )

        # Le démarrage devrait échouer car aucun receiver
        assert success is False

        # Vérifier le message d'erreur dans les logs
        logs = engine.get_logs()
        error_logs = [log for log in logs if "aucun receiver" in log["message"].lower()]
        assert len(error_logs) > 0

    def test_load_replay_file(self, temp_replay_dir, sample_candles_file):
        """Vérifie qu'on peut charger un fichier de replay."""
        engine = ScenarioBasedMockExchange(replay_data_dir=temp_replay_dir)

        # Start en mode pull (pas de receiver nécessaire)
        success = engine.start_replay_from_file(sample_candles_file, mode="pull")

        assert success is True

        # Vérifier qu'on a chargé les candles
        status = engine.get_replay_status()
        assert status["total_candles"] == 3
        assert status["status"] == "running"

        engine.stop_replay()

    def test_get_candles(self, temp_replay_dir, sample_candles_file):
        """Vérifie qu'on peut récupérer les candles chargées."""
        engine = ScenarioBasedMockExchange(replay_data_dir=temp_replay_dir)
        engine.start_replay_from_file(sample_candles_file, mode="pull")

        candles = engine.get_candles()

        assert len(candles) == 3
        assert candles[0]["open"] == 50000
        assert candles[1]["open"] == 50100
        assert candles[2]["open"] == 50200

        engine.stop_replay()
