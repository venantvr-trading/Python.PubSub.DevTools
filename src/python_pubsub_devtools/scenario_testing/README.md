# Scenario Testing Framework 🎯

Framework de tests déclaratifs avec chaos engineering intégré pour Python.PubSub.Risk.

## 🎯 Concept

Le Scenario Testing Framework permet de :

- ✅ **Définir des tests en YAML** : Tests déclaratifs sans code Python
- ✅ **Chaos Engineering** : Injection de pannes, délais, modifications d'événements
- ✅ **Assertions puissantes** : Vérification automatique des résultats
- ✅ **Intégration** : Combine EventRecorder + MockExchange
- ✅ **Rapports détaillés** : JSON/HTML avec timeline complète
- 🌐 **Web Dashboard** interactif (port 5558)

## 🌐 Web Dashboard (Port 5558) ⭐

Un dashboard web interactif pour exécuter et monitorer les tests de scénarios en temps réel.

```bash
# Lancer le dashboard
python tools/scenario_testing/serve_testing.py

# Ouvrir dans le navigateur
open http://localhost:5558
```

### Fonctionnalités du Dashboard

- **📋 Liste de Scénarios** : Sélectionner parmi les scénarios YAML disponibles
- **👁️ Prévisualisation** : Voir la configuration YAML avant exécution
- **▶️ Exécution** : Lancer les tests avec options (verbose, recording)
- **📊 Résultats en temps réel** :
    - Status du test (Running/Passed/Failed)
    - Durée d'exécution
    - Assertions réussies/totales
    - Nombre d'événements enregistrés
- **📝 Log d'Exécution** : Voir les logs en temps réel avec niveaux (INFO/SUCCESS/ERROR/WARNING)
- **✅ Liste d'Assertions** : Visualiser chaque assertion avec résultat détaillé
- **🔥 Rapport Chaos** : Statistiques sur les événements retardés, supprimés, pannes injectées
- **🎨 Design unifié** : Même charte graphique que les autres outils

### API REST

Le dashboard expose une API REST pour intégration programmatique :

```python
import requests

# Lister les scénarios disponibles
scenarios = requests.get('http://localhost:5558/api/scenarios').json()

# Lancer un test
response = requests.post('http://localhost:5558/api/run', json={
    'scenario': 'flash_crash_recovery.yaml',
    'verbose': True,
    'recording': True
})
test_id = response.json()['test_id']

# Obtenir le status
status = requests.get(f'http://localhost:5558/api/status/{test_id}').json()
print(f"Status: {status['status']}")
print(f"Assertions: {status['assertions_passed']}/{status['assertions_total']}")

# Arrêter le test
requests.post(f'http://localhost:5558/api/stop/{test_id}')
```

### Intégration

- **Port** : 5558
- **Liens** : Navigation vers Event Flow (5555), Recorder (5556), Exchange (5557)
- **Tests** : `tests/tools/test_serve_testing.py` (10 tests passing)

---

## 📋 Structure d'un scénario

```yaml
name: "Nom du test"
description: "Description détaillée"

setup:
  exchange:
    scenario: flash_crash  # Scénario de marché
    initial_price: 50000.0

  bot:
    initial_capital: 10000.0
    pool_count: 5

chaos:
  - type: delay_event
    event: IndicatorsCalculated
    delay_ms: 5000
    at_cycle: 25

steps:
  - wait_for_cycles: 50

  - assert:
      event_count:
        PositionPurchased: {min: 3}
      no_panic_sell: true
```

## 🚀 Usage Rapide

### CLI

```bash
# Lancer un scénario
python tools/scenario_testing/scenario_runner.py scenarios/flash_crash_recovery.yaml

# Avec sortie JSON
python scenario_runner.py scenarios/bull_run_profit.yaml --output results.json

# Mode verbose
python scenario_runner.py scenarios/chaos_resilience.yaml --verbose
```

### Programmatique

```python
from scenario_runner import ScenarioRunner

runner = ScenarioRunner("scenarios/flash_crash_recovery.yaml")
results = runner.run()

print(f"Status: {results['status']}")
print(f"Assertions: {results['assertions']['passed']}/{results['assertions']['total']}")
```

## 📦 Composants

### 1. Scenario Schema (`scenario_schema.py`)

Définit la structure des scénarios avec Pydantic :

```python
from scenario_schema import TestScenario, Setup, ExchangeSetup

scenario = TestScenario(
    name="Mon test",
    description="Test programmatique",
    setup=Setup(
        exchange=ExchangeSetup(
            scenario="volatile",
            initial_price=50000.0
        )
    ),
    steps=[{"wait_for_cycles": 30}]
)
```

### 2. Chaos Injector (`chaos_injector.py`)

Intercepte le service bus pour injecter du chaos :

**Types de chaos disponibles** :

| Type              | Description                        | Exemple                |
|-------------------|------------------------------------|------------------------|
| `delay_event`     | Retarde un événement               | Latence réseau simulée |
| `inject_failure`  | Injecte un événement Failed        | Crash de l'exchange    |
| `drop_event`      | Supprime un événement              | Perte de paquets       |
| `modify_event`    | Modifie les données d'un événement | Prix corrompus         |
| `network_latency` | Simule latence réseau globale      | Connexion lente        |

**Exemple** :

```yaml
chaos:
  # Delay spécifique
  - type: delay_event
    event: IndicatorsCalculated
    delay_ms: 5000
    at_cycle: 25

  # Injection de panne
  - type: inject_failure
    event: MarketPriceFetchFailed
    at_cycle: 30
    error_message: "Simulated timeout"

  # Drop aléatoire
  - type: drop_event
    event: BuyConditionMet
    probability: 0.3  # 30% de chance

  # Latence réseau
  - type: network_latency
    min_delay_ms: 100
    max_delay_ms: 1000
    at_cycle: 20
    duration_cycles: 10
```

### 3. Assertion Checker (`assertion_checker.py`)

Vérifie les conditions de test :

**Types d'assertions** :

#### `event_count` - Compter les événements

```yaml
assert:
  event_count:
    PositionPurchased:
      min: 3
      max: 10
      exact: 5
    PositionSold:
      max: 2
```

#### `event_sequence` - Vérifier l'ordre

```yaml
assert:
  event_sequence:
    - BotMonitoringCycleStarted
    - MarketPriceFetched
    - IndicatorsCalculated
    - BuyConditionMet
```

#### `no_panic_sell` - Pas de vente panique

```yaml
assert:
  no_panic_sell:
    crash_start_cycle: 20
    crash_end_cycle: 30
```

#### `final_capital` - Capital final

```yaml
assert:
  final_capital:
    min: 9000.0
    max: 12000.0
```

#### `position_count` - Positions ouvertes

```yaml
assert:
  position_count:
    min: 3
    max: 10
```

#### `custom` - Assertion personnalisée

```python
def assert_profitable_trade(events):
    purchases = [e for e in events if e['event_name'] == 'PositionPurchased']
    sales = [e for e in events if e['event_name'] == 'PositionSold']

    if not purchases or not sales:
        return False, "No trades"

    profit = sales[0]['event_data']['sale_price'] - purchases[0]['event_data']['purchase_price']
    return profit > 0, f"Profit: {profit}"


checker = AssertionChecker(events)
checker._check_custom_assertion(assert_profitable_trade)
```

### 4. Scenario Runner (`scenario_runner.py`)

Orchestrateur principal qui :

1. Charge le scénario YAML
2. Configure MockExchange + EventRecorder
3. Démarre ChaosInjector
4. Exécute les steps
5. Vérifie les assertions
6. Génère le rapport

## 📝 Scénarios Exemples

### 1. Flash Crash Recovery

```yaml
name: "Flash Crash Recovery Test"
description: "Verify bot handles flash crash without panic selling"

setup:
  exchange:
    scenario: flash_crash
    initial_price: 50000.0

chaos:
  - type: delay_event
    event: IndicatorsCalculated
    delay_ms: 5000
    at_cycle: 25

steps:
  - wait_for_cycles: 50

  - assert:
      event_count:
        PositionPurchased: {min: 3}
        PositionSold: {max: 2}
      no_panic_sell:
        crash_start_cycle: 20
        crash_end_cycle: 30
```

### 2. Bull Run Profit

```yaml
name: "Bull Run Profit Maximization"
description: "Verify bot capitalizes on bull run"

setup:
  exchange:
    scenario: bull_run
    initial_price: 50000.0

chaos: []  # Clean test

steps:
  - wait_for_cycles: 100

  - assert:
      event_count:
        PositionPurchased: {min: 10}
        PositionSold: {min: 5}
      final_capital:
        min: 10500.0  # 5% profit
```

### 3. Chaos Resilience

```yaml
name: "Chaos Resilience Test"
description: "Stress test with aggressive chaos"

setup:
  exchange:
    scenario: volatile
    initial_price: 50000.0
    volatility_multiplier: 2.0

chaos:
  # Drop events
  - type: drop_event
    event: IndicatorsCalculated
    probability: 0.2

  # Multiple failures
  - type: inject_failure
    event: MarketPriceFetchFailed
    at_cycle: 15

  - type: inject_failure
    event: MarketPriceFetchFailed
    at_cycle: 25

  # Heavy latency
  - type: network_latency
    min_delay_ms: 500
    max_delay_ms: 2000
    at_cycle: 20
    duration_cycles: 10

steps:
  - wait_for_cycles: 60

  - assert:
      event_count:
        MarketPriceFetchFailed: {min: 2}
        BotMonitoringCycleStarted: {min: 60}
      final_capital:
        min: 8000.0  # Max 20% loss acceptable
```

## 🎛️ Configuration

### Exchange Setup

```yaml
setup:
  exchange:
    scenario: flash_crash       # Scénario de marché
    initial_price: 50000.0       # Prix initial
    pair: "BTC/USDT"             # Paire
    volatility_multiplier: 1.0   # Multiplicateur de volatilité
    spread_bps: 20               # Spread en basis points
```

### Bot Setup

```yaml
setup:
  bot:
    initial_capital: 10000.0  # Capital initial
    pool_count: 5             # Nombre de pools
    poll_interval: 60         # Intervalle de polling
```

### Recording Setup

```yaml
setup:
  recording:
    enabled: true
    output: "recordings/{scenario_name}.json"
```

### Report Setup

```yaml
setup:
  report:
    format: html  # json, html, markdown
    output: "reports/{scenario_name}.html"
    include_events: true
    include_statistics: true
```

## 🔍 Étapes (Steps)

### `wait_for_cycles` - Attendre N cycles

```yaml
- wait_for_cycles: 50
```

### `wait_for_event` - Attendre un événement

```yaml
- wait_for_event: PositionPurchased
  timeout_seconds: 300
```

### `wait_for_time` - Attendre une durée

```yaml
- wait_for_time: 60  # 60 secondes
```

### `assert` - Vérifier des assertions

```yaml
- assert:
    event_count:
      PositionPurchased: {min: 3}
```

## 📊 Format des Résultats

```json
{
  "scenario": {
    "name": "Flash Crash Recovery Test",
    "description": "..."
  },
  "status": "passed",
  "duration_seconds": 12.34,
  "start_time": "2025-10-12T10:00:00+00:00",
  "end_time": "2025-10-12T10:00:12+00:00",
  "assertions": {
    "total": 5,
    "passed": 5,
    "failed": 0,
    "results": [
      {
        "name": "event_count.PositionPurchased.min",
        "passed": true,
        "message": "Expected at least 3 PositionPurchased events, got 5",
        "expected": ">= 3",
        "actual": 5
      }
    ]
  },
  "chaos": {
    "events_delayed": 1,
    "events_dropped": 0,
    "failures_injected": 0,
    "total_delay_ms": 5000
  },
  "exchange": {
    "min_price": 48500.0,
    "max_price": 52000.0,
    "total_return_pct": 2.5
  }
}
```

## 🧪 Tests

```bash
# Lancer les tests du framework
python -m pytest tests/tools/test_scenario_testing.py -v

# Tests actuels: 16/16 passing
```

## 💡 Cas d'Usage

### 1. Test de Non-Régression

```yaml
name: "Regression Test - Baseline"
description: "Ensure bot maintains baseline performance"

setup:
  exchange:
    scenario: sideways
    initial_price: 50000.0

chaos: []

steps:
  - wait_for_cycles: 100

  - assert:
      event_count:
        BotMonitoringCycleStarted: {exact: 100}
        PositionPurchased: {min: 5, max: 15}
      final_capital:
        min: 9800.0  # Max 2% loss on sideways market
```

### 2. Stress Test

```yaml
name: "Stress Test - High Load"
description: "Test under extreme conditions"

setup:
  exchange:
    scenario: volatile
    volatility_multiplier: 5.0  # 5x normal
    spread_bps: 100  # 1% spread

chaos:
  - type: network_latency
    min_delay_ms: 1000
    max_delay_ms: 5000
    at_cycle: 1
    duration_cycles: 200

steps:
  - wait_for_cycles: 200

  - assert:
      event_count:
        BotMonitoringCycleStarted: {min: 200}
      final_capital:
        min: 7000.0  # Survive with max 30% loss
```

### 3. Recovery Test

```yaml
name: "Recovery Test - After Failure"
description: "Verify bot recovers from failures"

setup:
  exchange:
    scenario: bull_run
    initial_price: 50000.0

chaos:
  # Inject 5 consecutive failures
  - type: inject_failure
    event: MarketPriceFetchFailed
    at_cycle: 10
  - type: inject_failure
    event: MarketPriceFetchFailed
    at_cycle: 11
  - type: inject_failure
    event: MarketPriceFetchFailed
    at_cycle: 12
  - type: inject_failure
    event: MarketPriceFetchFailed
    at_cycle: 13
  - type: inject_failure
    event: MarketPriceFetchFailed
    at_cycle: 14

steps:
  - wait_for_cycles: 100

  - assert:
      event_count:
        MarketPriceFetchFailed: {exact: 5}
        BotMonitoringCycleStarted: {min: 105}  # Should restart
        PositionPurchased: {min: 5}  # Should still trade
```

### 4. Comparison Test

```python
# Compare strategies across scenarios
scenarios = ["bull_run", "bear_crash", "sideways", "volatile"]

for scenario in scenarios:
    runner = ScenarioRunner(f"scenarios/{scenario}_test.yaml")
    results = runner.run()

    print(f"{scenario}: {results['assertions']['passed']}/{results['assertions']['total']}")
```

## 🎨 Best Practices

1. **Nommer clairement** : Utilisez des noms descriptifs pour les scénarios
2. **Tester les edge cases** : Flash crashes, pannes, latence
3. **Isoler les tests** : Un scénario = un aspect testé
4. **Utiliser le chaos** : Testez la résilience avec chaos engineering
5. **Vérifier les recordings** : Rejouez les scénarios problématiques
6. **Automatiser** : Lancez tous les scénarios en CI/CD

## 📚 Intégration avec les autres outils

### Avec EventRecorder

Le ScenarioRunner enregistre automatiquement tous les événements si activé :

```yaml
setup:
  recording:
    enabled: true
    output: "recordings/{scenario_name}.json"
```

Ensuite, rejouez :

```python
from event_recorder import EventReplayer

replayer = EventReplayer("recordings/flash_crash_recovery.json")
replayer.replay(service_bus, speed_multiplier=10.0)
```

### Avec MockExchange

Le ScenarioRunner utilise automatiquement MockExchange :

```yaml
setup:
  exchange:
    scenario: pump_and_dump  # Utilise ScenarioBasedMockExchange
    initial_price: 50000.0
```

Tous les scénarios de MockExchange sont disponibles :

- `bull_run`, `bear_crash`, `sideways`
- `flash_crash`, `volatile`
- `pump_and_dump`, `dead_cat_bounce`
- `accumulation`, `distribution`
- `irregular_candles`

## 🔧 Développement

### Ajouter un nouveau type de chaos

1. Ajouter le modèle dans `scenario_schema.py` :

```python
class CustomChaos(BaseModel):
    type: Literal["custom_chaos"] = "custom_chaos"
    param1: str
    param2: int

ChaosAction = Union[..., CustomChaos]
```

2. Implémenter dans `chaos_injector.py` :

```python
def _apply_chaos(self, event_name, event, source):
    # ...
    elif isinstance(action, CustomChaos):
    self._apply_custom_chaos(action, event_name, event)
```

### Ajouter un nouveau type d'assertion

1. Ajouter la méthode dans `assertion_checker.py` :

```python
def _check_custom_assertion(self, config: Dict[str, Any]):
    # Implementation
    self.results.append(AssertionResult(...))
```

2. Enregistrer dans `check_assertions` :

```python
def check_assertions(self, assertions: Dict[str, Any]):
    # ...
    elif key == "custom_assertion":
    self._check_custom_assertion(value)
```

## ⚠️ Limitations

- Les scénarios sont simulés (pas de vraie connexion exchange)
- Le chaos injector nécessite un service bus mockable
- Les assertions custom nécessitent du code Python
- Pas de parallélisation des scénarios (pour l'instant)

## 🚧 Améliorations Futures

- [ ] Support de données historiques réelles
- [ ] Parallélisation des scénarios
- [ ] Dashboard web en temps réel
- [ ] Génération automatique de scénarios
- [ ] Machine learning pour détecter les patterns d'échec
- [ ] Intégration avec Grafana/Prometheus
- [ ] Support de scénarios distribués (multi-bots)

## 📚 Voir Aussi

- **Event Recorder** : `tools/event_recorder/` - Enregistrement d'événements
- **Mock Exchange** : `tools/mock_exchange/` - Exchange simulé
- **Event Flow** : `tools/event_flow/` - Visualisation du graphe

---

**Status** : ✅ Production-ready
**Tests** : ✅ 16/16 passing
**Documentation** : ✅ Complete
