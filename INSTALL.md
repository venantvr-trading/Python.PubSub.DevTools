# Installation et Utilisation

## Installation

### Installation depuis PyPI (recommandé)

```bash
pip install python-pubsub-devtools
```

### Installation depuis le code source

```bash
# Clone le repository
git clone https://github.com/venantvr-trading/Python.PubSub.DevTools.git
cd Python.PubSub.DevTools

# Installation en mode développement
pip install -e .

# Ou installation standard
pip install .
```

### Installation depuis le package distribué

```bash
# Depuis le wheel
pip install dist/python_pubsub_devtools-0.1.0-py3-none-any.whl

# Ou depuis le tarball
pip install dist/python_pubsub_devtools-0.1.0.tar.gz
```

## Vérification de l'installation

Après installation, vérifiez que le CLI est disponible :

```bash
pubsub-tools --help
pubsub-tools version
```

## Utilisation du CLI

### Commandes disponibles

```bash
# Afficher l'aide
pubsub-tools --help

# Lancer le visualiseur de flux d'événements
pubsub-tools event-flow --config devtools_config.yaml

# Lancer l'enregistreur d'événements
pubsub-tools event-recorder --config devtools_config.yaml

# Lancer le simulateur d'échange
pubsub-tools mock-exchange --config devtools_config.yaml

# Lancer le tableau de bord de test de scénarios
pubsub-tools test-scenarios --config devtools_config.yaml

# Voir toutes les options de dashboard
pubsub-tools dashboard --config devtools_config.yaml

# Commandes de métriques
pubsub-tools metrics collect
pubsub-tools metrics export --format json
```

### Configuration

Créez un fichier de configuration `devtools_config.yaml` :

```bash
cp examples/config.example.yaml devtools_config.yaml
```

Éditez le fichier selon vos besoins.

## Utilisation comme bibliothèque Python

```python
from python_pubsub_devtools import (
    DevToolsConfig,
    EventFlowAnalyzer,
    EventRecorder,
    ScenarioBasedMockExchange,
    ScenarioRunner,
)

# Charger la configuration
config = DevToolsConfig.from_yaml("devtools_config.yaml")

# Utiliser les composants
analyzer = EventFlowAnalyzer(config.event_flow)
recorder = EventRecorder(config.event_recorder)

# Utiliser les utilitaires de trading
from python_pubsub_devtools import calculate_sma, calculate_rsi

prices = [100, 102, 101, 105, 107]
sma = calculate_sma(prices, period=3)
rsi = calculate_rsi(prices, period=14)
```

## Lancement des serveurs

### Serveur Event Flow
```bash
pubsub-tools event-flow --port 5001
```
Accédez à http://localhost:5001

### Serveur Event Recorder
```bash
pubsub-tools event-recorder --port 5002
```
Accédez à http://localhost:5002

### Serveur Mock Exchange
```bash
pubsub-tools mock-exchange --port 5003
```
Accédez à http://localhost:5003

### Serveur Scenario Testing
```bash
pubsub-tools test-scenarios --port 5004
```
Accédez à http://localhost:5004

## Dépendances

Les dépendances suivantes sont automatiquement installées :

- flask>=2.0.0
- pyyaml>=6.0
- pydantic>=2.0
- pandas>=2.0.0
- pydot>=1.4.0

## Développement

Pour développer sur ce package :

```bash
# Installer avec les dépendances de développement
pip install -e ".[dev]"

# Lancer les tests
pytest

# Vérifier le code
make lint

# Construire le package
python -m build
```

## Distribution

### Créer une nouvelle version

```bash
# Nettoyer les anciens builds
make clean

# Construire les packages
python -m build

# Les packages sont créés dans dist/
# - python_pubsub_devtools-X.Y.Z.tar.gz (source)
# - python_pubsub_devtools-X.Y.Z-py3-none-any.whl (wheel)
```

### Publier sur PyPI

```bash
# Installer twine si nécessaire
pip install twine

# Vérifier les packages
twine check dist/*

# Publier sur TestPyPI (recommandé pour test)
twine upload --repository testpypi dist/*

# Publier sur PyPI
twine upload dist/*
```

## Contenu du package

Le package inclut :

- **Code source** : Tous les modules Python
- **Templates web** : Fichiers HTML pour les dashboards
- **Assets statiques** : CSS et JavaScript
- **Documentation** : Fichiers Markdown
- **Exemples** : Scripts d'exemple et configurations
- **Tests** : Suite de tests complète

## Support

Pour obtenir de l'aide :

- Documentation : https://github.com/venantvr-trading/Python.PubSub.DevTools/wiki
- Issues : https://github.com/venantvr-trading/Python.PubSub.DevTools/issues
- README : Voir README.md pour plus de détails
