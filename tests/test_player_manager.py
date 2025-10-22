"""Tests pour PlayerManager - vérifie qu'on poste bien aux applications enregistrées."""
from unittest.mock import Mock, patch, call

from python_pubsub_devtools.event_recorder.player_manager import PlayerManager


class TestPlayerManager:
    """Tests pour la gestion des players et le replay."""

    def test_register_player(self):
        """Vérifie qu'un player peut s'enregistrer."""
        manager = PlayerManager()

        result = manager.register("TestBot", "http://localhost:8080/replay")

        assert result is True
        assert manager.count() == 1
        players = manager.get_all()
        assert len(players) == 1
        assert players[0]["consumer_name"] == "TestBot"
        assert players[0]["player_endpoint"] == "http://localhost:8080/replay"

    def test_register_multiple_players(self):
        """Vérifie qu'on peut enregistrer plusieurs players."""
        manager = PlayerManager()

        manager.register("Bot1", "http://localhost:8080/replay")
        manager.register("Bot2", "http://localhost:8081/replay")

        assert manager.count() == 2
        assert manager.has_players() is True

    def test_unregister_player(self):
        """Vérifie qu'on peut désenregistrer un player."""
        manager = PlayerManager()
        manager.register("TestBot", "http://localhost:8080/replay")

        consumer_name = manager.unregister("http://localhost:8080/replay")

        assert consumer_name == "TestBot"
        assert manager.count() == 0
        assert manager.has_players() is False

    @patch('python_pubsub_devtools.event_recorder.player_manager.requests.post')
    def test_replay_events_posts_to_registered_players(self, mock_post):
        """Vérifie que replay_events poste bien aux players enregistrés via HTTP POST."""
        # Setup
        manager = PlayerManager()
        manager.register("Bot1", "http://localhost:8080/replay")
        manager.register("Bot2", "http://localhost:8081/replay")

        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        events = [
            {
                "timestamp_offset_ms": 0,
                "event_name": "MarketOpened",
                "event_data": {"symbol": "BTC", "price": 50000},
                "source": "MockExchange"
            },
            {
                "timestamp_offset_ms": 100,
                "event_name": "PriceUpdated",
                "event_data": {"symbol": "BTC", "price": 50100},
                "source": "MockExchange"
            }
        ]

        # Execute
        result = manager.replay_events(events, speed=100.0)

        # Verify
        assert result["replayed_count"] == 4  # 2 events × 2 players
        assert result["failed_count"] == 0

        # Vérifier que requests.post a été appelé 4 fois (2 events × 2 players)
        assert mock_post.call_count == 4

        # Vérifier les appels pour le premier événement
        expected_calls = [
            call(
                "http://localhost:8080/replay",
                json={
                    "event_name": "MarketOpened",
                    "event_data": {"symbol": "BTC", "price": 50000},
                    "source": "MockExchange"
                },
                timeout=5
            ),
            call(
                "http://localhost:8081/replay",
                json={
                    "event_name": "MarketOpened",
                    "event_data": {"symbol": "BTC", "price": 50000},
                    "source": "MockExchange"
                },
                timeout=5
            ),
        ]

        # Vérifier que les 2 premiers appels correspondent
        actual_calls = mock_post.call_args_list[:2]
        assert actual_calls == expected_calls

    @patch('python_pubsub_devtools.event_recorder.player_manager.requests.post')
    def test_replay_events_to_specific_player(self, mock_post):
        """Vérifie qu'on peut cibler un player spécifique."""
        manager = PlayerManager()
        manager.register("Bot1", "http://localhost:8080/replay")
        manager.register("Bot2", "http://localhost:8081/replay")

        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        events = [
            {
                "timestamp_offset_ms": 0,
                "event_name": "TestEvent",
                "event_data": {},
                "source": "Test"
            }
        ]

        # Cibler seulement Bot1
        result = manager.replay_events(events, target_player="Bot1")

        # Verify
        assert result["replayed_count"] == 1
        assert mock_post.call_count == 1

        # Vérifier que seul Bot1 a reçu l'événement
        mock_post.assert_called_once_with(
            "http://localhost:8080/replay",
            json={
                "event_name": "TestEvent",
                "event_data": {},
                "source": "Test"
            },
            timeout=5
        )

    @patch('python_pubsub_devtools.event_recorder.player_manager.requests.post')
    def test_replay_handles_http_errors(self, mock_post):
        """Vérifie qu'on gère les erreurs HTTP."""
        import requests

        manager = PlayerManager()
        manager.register("FailingBot", "http://localhost:9999/replay")

        # Simuler une erreur de connexion
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        events = [
            {
                "timestamp_offset_ms": 0,
                "event_name": "TestEvent",
                "event_data": {},
                "source": "Test"
            }
        ]

        result = manager.replay_events(events)

        assert result["replayed_count"] == 0
        assert result["failed_count"] == 1

    def test_replay_with_no_players_registered(self):
        """Vérifie qu'on retourne une erreur si aucun player enregistré."""
        manager = PlayerManager()

        events = [
            {
                "timestamp_offset_ms": 0,
                "event_name": "Test",
                "event_data": {},
                "source": "Test"
            }
        ]

        result = manager.replay_events(events)

        assert result["replayed_count"] == 0
        assert "error" in result
        assert result["error"] == "No players registered"
