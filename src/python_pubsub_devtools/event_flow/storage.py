"""
Graph Data Storage - In-memory cache for event flow graphs

Stores precomputed DOT and SVG data for different graph types.
"""
from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class GraphData:
    """Container for graph data with metadata"""

    graph_type: str
    dot_content: str
    svg_content: Optional[str] = None
    namespaces: Set[str] = field(default_factory=set)
    stats: Dict[str, int] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert set to list for JSON
        data['namespaces'] = sorted(list(self.namespaces))
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> GraphData:
        """Create from dictionary"""
        # Convert list back to set
        if 'namespaces' in data and data['namespaces'] is not None:
            data['namespaces'] = set(data['namespaces'])
        else:
            data['namespaces'] = set()
        return cls(**data)


class GraphStorage:
    """
    Thread-safe in-memory storage for graph data with optional disk persistence.
    """

    def __init__(self, persist_path: Optional[Path] = None):
        """
        Initialize storage.

        Args:
            persist_path: Optional path to persist cache to disk.
        """
        self._graphs: Dict[str, GraphData] = {}
        self._lock = threading.RLock()
        self._persist_path = persist_path

        if self._persist_path:
            self._load_from_disk()

    def store(self, graph_data: GraphData) -> None:
        """Store graph data and persist to disk if configured."""
        with self._lock:
            self._graphs[graph_data.graph_type] = graph_data
            if self._persist_path:
                self._save_to_disk()

    def get(self, graph_type: str) -> Optional[GraphData]:
        """Retrieve graph data by type."""
        with self._lock:
            return self._graphs.get(graph_type)

    def get_all(self) -> Dict[str, GraphData]:
        """Retrieve all stored graphs."""
        with self._lock:
            return self._graphs.copy()

    def clear(self, graph_type: Optional[str] = None) -> None:
        """
        Clear cached graphs.

        Args:
            graph_type: If specified, clear only this graph type. Otherwise clear all.
        """
        with self._lock:
            if graph_type:
                self._graphs.pop(graph_type, None)
            else:
                self._graphs.clear()

            if self._persist_path:
                self._save_to_disk()

    def get_status(self) -> Dict:
        """Get cache status information."""
        with self._lock:
            status = {
                'total_graphs': len(self._graphs),
                'persist_enabled': self._persist_path is not None,
                'persist_path': str(self._persist_path) if self._persist_path else None,
                'graphs': {},
            }

            for graph_type, data in self._graphs.items():
                status['graphs'][graph_type] = {
                    'timestamp': data.timestamp,
                    'has_svg': data.svg_content is not None,
                    'stats': data.stats,
                    'namespaces': sorted(list(data.namespaces))
                }
            return status

    def _save_to_disk(self) -> None:
        """Save cache to disk as JSON using an atomic write."""
        if not self._persist_path:
            return

        with self._lock:
            try:
                self._persist_path.parent.mkdir(parents=True, exist_ok=True)
                data = {gt: gd.to_dict() for gt, gd in self._graphs.items()}

                temp_path = self._persist_path.with_suffix('.tmp')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                temp_path.replace(self._persist_path)
                logger.debug(f"Cache saved to {self._persist_path}")
            except (IOError, OSError) as e:
                logger.error(f"Failed to persist cache to disk: {e}")

    def _load_from_disk(self) -> None:
        """Load cache from disk if it exists."""
        if not self._persist_path or not self._persist_path.exists():
            return

        with self._lock:
            try:
                with open(self._persist_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._graphs = {gt: GraphData.from_dict(gd) for gt, gd in data.items()}
                logger.info(f"Cache loaded from {self._persist_path}")
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Failed to load cache from disk ({self._persist_path}): {e}")
                self._graphs = {}


# --- Singleton Pattern for Global Access ---

_storage_instance: Optional[GraphStorage] = None
_storage_lock = threading.Lock()


def initialize_storage(config) -> GraphStorage:
    """
    Initialize the global storage instance using the application config.
    This should be called once at application startup.
    """
    global _storage_instance
    with _storage_lock:
        if _storage_instance is None:
            persist_path = getattr(config, 'cache_persist_path', None)  # config is of type EventFlowConfig
            _storage_instance = GraphStorage(persist_path=persist_path)
            logger.info(f"GraphStorage initialized. Persistence: {persist_path or 'Disabled'}")
    return _storage_instance


def get_storage() -> GraphStorage:
    """
    Get the global storage instance (singleton).

    Raises:
        RuntimeError: If the storage has not been initialized.

    Returns:
        The singleton GraphStorage instance.
    """
    if _storage_instance is None:
        raise RuntimeError(
            "GraphStorage not initialized. Call initialize_storage() at startup."
        )
    return _storage_instance


def reset_storage() -> None:
    """Reset the global storage instance. Primarily for testing."""
    global _storage_instance
    with _storage_lock:
        _storage_instance = None
        logger.debug("Global GraphStorage instance has been reset.")