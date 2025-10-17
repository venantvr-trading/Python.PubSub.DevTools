"""
Proxy HTTP pour communiquer avec ServiceBus dans un autre processus.
"""
from __future__ import annotations

from typing import Any

import requests


class ServiceBusHttpProxy:
    """Proxy qui communique avec ServiceBus via HTTP API.

    Utilisé quand DevTools et l'application tournent dans des processus séparés.

    Args:
        host: Hôte du ServiceBus (défaut: localhost)
        port: Port de l'API HTTP du ServiceBus (défaut: 8765)
    """

    def __init__(self, host: str = 'localhost', port: int = 8765):
        self.host = host
        self.port = port
        self.base_url = f'http://{host}:{port}'

    def publish(self, event_name: str, event: Any, source: str) -> None:
        """Publie un événement sur le ServiceBus distant via HTTP.

        Args:
            event_name: Nom de l'événement
            event: Données de l'événement (dict ou objet avec model_dump())
            source: Source de l'événement
        """
        # Sérialiser l'événement
        if hasattr(event, 'model_dump'):
            event_data = event.model_dump()
        elif hasattr(event, '__dict__'):
            event_data = event.__dict__
        elif isinstance(event, dict):
            event_data = event
        else:
            event_data = {'value': str(event)}

        # Envoyer au ServiceBus distant
        try:
            response = requests.post(
                f'{self.base_url}/api/publish',
                json={
                    'event_name': event_name,
                    'event_data': event_data,
                    'source': source
                },
                timeout=5
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to publish event to ServiceBus: {e}")
            raise

    def __repr__(self) -> str:
        return f"ServiceBusHttpProxy({self.host}:{self.port})"
