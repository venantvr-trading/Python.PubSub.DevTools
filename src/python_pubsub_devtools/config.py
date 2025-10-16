"""
Configuration centralisée pour PubSub DevTools avec support Pydantic et YAML.
"""
from pathlib import Path
from typing import Dict, List, Any

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class EventFlowConfig(BaseModel):
    """Configuration pour le service de visualisation Event Flow.

    Attributes:
        agents_dir: Répertoire contenant les fichiers Python des agents
        events_dir: Répertoire contenant les fichiers JSON des événements
        port: Port d'écoute du serveur web (défaut: 5555)
        test_agents: Liste des agents à exclure de la visualisation
        namespace_colors: Couleurs par namespace pour la visualisation
    """
    agents_dir: Path
    events_dir: Path
    port: int = 5555
    test_agents: List[str] = Field(default_factory=list)
    namespace_colors: Dict[str, str] = Field(default_factory=lambda: {
        'trading': '#4caf50',
        'risk': '#ff9800',
        'monitoring': '#2196f3',
        'commands': '#9c27b0',
        'execution': '#f44336',
        'unknown': '#e0e0e0'
    })

    @field_validator('agents_dir', 'events_dir', mode='before')
    @classmethod
    def convert_to_path(cls, v: Any) -> Path:
        """Convertit les chemins en objets Path."""
        if isinstance(v, str):
            return Path(v)
        return v


class EventRecorderConfig(BaseModel):
    """Configuration pour le service Event Recorder.

    Attributes:
        recordings_dir: Répertoire des enregistrements d'événements
        port: Port d'écoute du serveur web (défaut: 5556)
    """
    recordings_dir: Path
    port: int = 5556

    @field_validator('recordings_dir', mode='before')
    @classmethod
    def convert_to_path(cls, v: Any) -> Path:
        """Convertit le chemin en objet Path."""
        if isinstance(v, str):
            return Path(v)
        return v


class MockExchangeConfig(BaseModel):
    """Configuration pour le simulateur Mock Exchange.

    Attributes:
        port: Port d'écoute du serveur web (défaut: 5557)
        default_initial_price: Prix initial par défaut pour les actifs
        default_volatility: Volatilité par défaut
        default_spread_bps: Spread par défaut en points de base
    """
    port: int = 5557
    default_initial_price: float = 50000.0
    default_volatility: float = 0.02
    default_spread_bps: float = 10.0


class ScenarioTestingConfig(BaseModel):
    """Configuration pour le moteur de tests de scénarios.

    Attributes:
        scenarios_dir: Répertoire des fichiers de scénarios YAML
        reports_dir: Répertoire de sortie des rapports de tests
        port: Port d'écoute du serveur web (défaut: 5558)
    """
    scenarios_dir: Path
    reports_dir: Path
    port: int = 5558

    @field_validator('scenarios_dir', 'reports_dir', mode='before')
    @classmethod
    def convert_to_path(cls, v: Any) -> Path:
        """Convertit les chemins en objets Path."""
        if isinstance(v, str):
            return Path(v)
        return v


class DevToolsConfig(BaseModel):
    """Configuration principale pour tous les services DevTools.

    Cette classe sert de point d'entrée unique pour la configuration de tous les outils.
    Elle peut être chargée depuis un fichier YAML et résout automatiquement les chemins
    relatifs par rapport au fichier de configuration.

    Attributes:
        agents_dir: Répertoire contenant les fichiers Python des agents
        events_dir: Répertoire contenant les fichiers JSON des événements
        recordings_dir: Répertoire des enregistrements d'événements
        scenarios_dir: Répertoire des fichiers de scénarios
        reports_dir: Répertoire des rapports de tests
        event_flow: Configuration spécifique pour Event Flow
        event_recorder: Configuration spécifique pour Event Recorder
        mock_exchange: Configuration spécifique pour Mock Exchange
        scenario_testing: Configuration spécifique pour Scenario Testing
    """
    # Répertoires communs
    agents_dir: Path
    events_dir: Path
    recordings_dir: Path
    scenarios_dir: Path | None = None
    reports_dir: Path | None = None

    # Configurations par service
    event_flow: EventFlowConfig | None = None
    event_recorder: EventRecorderConfig | None = None
    mock_exchange: MockExchangeConfig | None = None
    scenario_testing: ScenarioTestingConfig | None = None

    @field_validator('agents_dir', 'events_dir', 'recordings_dir', 'scenarios_dir', 'reports_dir', mode='before')
    @classmethod
    def convert_to_path(cls, v: Any) -> Path | None:
        """Convertit les chemins en objets Path."""
        if v is None:
            return None
        if isinstance(v, str):
            return Path(v)
        return v

    @model_validator(mode='after')
    def build_service_configs(self) -> 'DevToolsConfig':
        """Construit les configurations par service si elles ne sont pas fournies."""
        # Event Flow
        if self.event_flow is None:
            self.event_flow = EventFlowConfig(
                agents_dir=self.agents_dir,
                events_dir=self.events_dir
            )
        else:
            # Assurer que agents_dir et events_dir sont définis
            if not hasattr(self.event_flow, 'agents_dir') or self.event_flow.agents_dir is None:
                self.event_flow.agents_dir = self.agents_dir
            if not hasattr(self.event_flow, 'events_dir') or self.event_flow.events_dir is None:
                self.event_flow.events_dir = self.events_dir

        # Event Recorder
        if self.event_recorder is None:
            self.event_recorder = EventRecorderConfig(
                recordings_dir=self.recordings_dir
            )
        else:
            if not hasattr(self.event_recorder, 'recordings_dir') or self.event_recorder.recordings_dir is None:
                self.event_recorder.recordings_dir = self.recordings_dir

        # Mock Exchange
        if self.mock_exchange is None:
            self.mock_exchange = MockExchangeConfig()

        # Scenario Testing
        if self.scenario_testing is None and self.scenarios_dir and self.reports_dir:
            self.scenario_testing = ScenarioTestingConfig(
                scenarios_dir=self.scenarios_dir,
                reports_dir=self.reports_dir
            )
        elif self.scenario_testing is not None:
            if not hasattr(self.scenario_testing, 'scenarios_dir') or self.scenario_testing.scenarios_dir is None:
                self.scenario_testing.scenarios_dir = self.scenarios_dir or Path('scenarios')
            if not hasattr(self.scenario_testing, 'reports_dir') or self.scenario_testing.reports_dir is None:
                self.scenario_testing.reports_dir = self.reports_dir or Path('reports')

        return self

    @classmethod
    def from_yaml(cls, filepath: str | Path) -> 'DevToolsConfig':
        """Charge la configuration depuis un fichier YAML.

        Les chemins relatifs dans le YAML sont résolus par rapport au répertoire
        contenant le fichier de configuration.

        Args:
            filepath: Chemin vers le fichier YAML de configuration

        Returns:
            Instance de DevToolsConfig validée et configurée

        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            yaml.YAMLError: Si le fichier YAML est mal formé
            pydantic.ValidationError: Si la configuration est invalide
        """
        config_path = Path(filepath).resolve()

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)

        # Résoudre les chemins relatifs par rapport au fichier de config
        config_dir = config_path.parent

        def resolve_path(path_value: Any) -> Any:
            """Résout un chemin relatif par rapport au répertoire de config."""
            if isinstance(path_value, str):
                p = Path(path_value)
                if not p.is_absolute():
                    return str(config_dir / p)
            return path_value

        # Résoudre les chemins de premier niveau
        for key in ['agents_dir', 'events_dir', 'recordings_dir', 'scenarios_dir', 'reports_dir']:
            if key in data:
                data[key] = resolve_path(data[key])

        # Résoudre les chemins dans les sous-configurations
        if 'event_flow' in data:
            for key in ['agents_dir', 'events_dir']:
                if key in data['event_flow']:
                    data['event_flow'][key] = resolve_path(data['event_flow'][key])

        if 'event_recorder' in data:
            if 'recordings_dir' in data['event_recorder']:
                data['event_recorder']['recordings_dir'] = resolve_path(data['event_recorder']['recordings_dir'])

        if 'scenario_testing' in data:
            for key in ['scenarios_dir', 'reports_dir']:
                if key in data['scenario_testing']:
                    data['scenario_testing'][key] = resolve_path(data['scenario_testing'][key])

        return cls(**data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DevToolsConfig':
        """Crée une configuration depuis un dictionnaire.

        Args:
            data: Dictionnaire de configuration

        Returns:
            Instance de DevToolsConfig validée
        """
        return cls(**data)
