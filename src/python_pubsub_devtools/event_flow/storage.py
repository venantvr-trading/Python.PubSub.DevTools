"""
Graph Data Storage - In-memory cache for event flow graphs

Stores precomputed DOT and SVG data for different graph types.
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Set


@dataclass
class GraphData:
    """Container for graph data with metadata"""

    graph_type: str
    dot_content: str
    svg_content: Optional[str] = None
    namespaces: Optional[Set[str]] = None
    stats: Optional[Dict[str, int]] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        """Initialize timestamp if not provided"""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        if self.namespaces:
            data['namespaces'] = list(self.namespaces)
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> GraphData:
        """Create from dictionary"""
        if 'namespaces' in data and data['namespaces']:
            data['namespaces'] = set(data['namespaces'])
        return cls(**data)


class GraphStorage:
    """
    Thread-safe in-memory storage for graph data

    Supports:
    - Storing multiple graph types (complete, full-tree)
    - Metadata about last update
    - Optional persistence to disk
    """

    def __init__(self, persist_path: Optional[Path] = None):
        """
        Initialize storage

        Args:
            persist_path: Optional path to persist cache to disk
        """
        self._graphs: Dict[str, GraphData] = {}
        self._lock = threading.RLock()
        self._persist_path = persist_path

        # Load from disk if available
        if self._persist_path and self._persist_path.exists():
            self._load_from_disk()

    def store(self, graph_data: GraphData) -> None:
        """
        Store graph data

        Args:
            graph_data: GraphData instance to store
        """
        with self._lock:
            self._graphs[graph_data.graph_type] = graph_data

            # Persist to disk if configured
            if self._persist_path:
                self._save_to_disk()

    def get(self, graph_type: str) -> Optional[GraphData]:
        """
        Retrieve graph data

        Args:
            graph_type: Type of graph (complete, full-tree)

        Returns:
            GraphData if found, None otherwise
        """
        with self._lock:
            return self._graphs.get(graph_type)

    def get_all(self) -> Dict[str, GraphData]:
        """
        Retrieve all stored graphs

        Returns:
            Dictionary mapping graph_type to GraphData
        """
        with self._lock:
            return self._graphs.copy()

    def has_graph(self, graph_type: str) -> bool:
        """
        Check if graph exists in cache

        Args:
            graph_type: Type of graph to check

        Returns:
            True if graph exists
        """
        with self._lock:
            return graph_type in self._graphs

    def clear(self, graph_type: Optional[str] = None) -> None:
        """
        Clear cached graphs

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
        """
        Get cache status information

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            status = {
                'total_graphs': len(self._graphs),
                'graphs': {},
                'persist_enabled': self._persist_path is not None,
            }

            for graph_type, graph_data in self._graphs.items():
                status['graphs'][graph_type] = {
                    'timestamp': graph_data.timestamp,
                    'has_svg': graph_data.svg_content is not None,
                    'stats': graph_data.stats,
                }

            return status

    def _save_to_disk(self) -> None:
        """Save cache to disk as JSON"""
        if not self._persist_path:
            return

        try:
            # Ensure parent directory exists
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to serializable format
            data = {
                graph_type: graph_data.to_dict()
                for graph_type, graph_data in self._graphs.items()
            }

            # Write to temp file then rename (atomic)
            temp_path = self._persist_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            temp_path.replace(self._persist_path)

        except Exception as e:
            print(f"Warning: Failed to persist cache to disk: {e}")

    def _load_from_disk(self) -> None:
        """Load cache from disk"""
        if not self._persist_path or not self._persist_path.exists():
            return

        try:
            with open(self._persist_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Reconstruct GraphData objects
            self._graphs = {
                graph_type: GraphData.from_dict(graph_dict)
                for graph_type, graph_dict in data.items()
            }

        except Exception as e:
            print(f"Warning: Failed to load cache from disk: {e}")
            self._graphs = {}


# Global storage instance (singleton pattern)
_storage_instance: Optional[GraphStorage] = None
_storage_lock = threading.Lock()


def get_storage(persist_path: Optional[Path] = None) -> GraphStorage:
    """
    Get the global storage instance (singleton)

    Args:
        persist_path: Optional path for persistence (only used on first call)

    Returns:
        GraphStorage instance
    """
    global _storage_instance

    if _storage_instance is None:
        with _storage_lock:
            if _storage_instance is None:
                _storage_instance = GraphStorage(persist_path=persist_path)

    return _storage_instance


def reset_storage() -> None:
    """Reset the global storage instance (primarily for testing)"""
    global _storage_instance
    with _storage_lock:
        _storage_instance = None
