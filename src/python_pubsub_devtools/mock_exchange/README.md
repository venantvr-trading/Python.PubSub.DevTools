# Scenario-Based Mock Exchange 🎰

Un exchange simulé avec des scénarios de marché réalistes pour le testing et le debugging.

## 🎯 Concept

Le Mock Exchange permet de simuler **10 scénarios de marché différents** avec des comportements prédéfinis :

- Mouvements réalistes de prix
- Génération de candles OHLCV
- Configuration du spread bid-ask
- Contrôle de la volatilité
- Candles irréguliers (pour tester la gestion d'erreurs)

## 📋 Scénarios Disponibles

| Scénario              | Description                      | Retour typique             | Usage                       |
|-----------------------|----------------------------------|----------------------------|-----------------------------|
| **BULL_RUN**          | Tendance haussière constante     | +20% sur 100 candles       | Tester les achats           |
| **BEAR_CRASH**        | Chute baissière                  | -30% sur 50 candles        | Tester les ventes           |
| **SIDEWAYS**          | Oscillation latérale             | ±2% autour du prix initial | Tester l'inactivité         |
| **FLASH_CRASH**       | Crash soudain puis récupération  | -15% puis retour           | Tester la résilience        |
| **VOLATILE**          | Haute volatilité                 | ±5% par candle             | Tester les limites          |
| **PUMP_AND_DUMP**     | Montée rapide puis crash         | +30% puis -40%             | Tester l'avidité            |
| **DEAD_CAT_BOUNCE**   | Chute, rebond, rechute           | -20%, +10%, -15%           | Tester les faux signaux     |
| **ACCUMULATION**      | Range serré puis breakout        | ±1% puis +15%              | Tester les breakouts        |
| **DISTRIBUTION**      | Range serré puis breakdown       | ±1% puis -15%              | Tester les breakdowns       |
| **IRREGULAR_CANDLES** | Intervalles de temps irréguliers | N/A                        | Tester la gestion d'erreurs |

## 🌐 Web Dashboard (Port 5557) ⭐

Un dashboard web interactif pour visualiser les simulations de marché en temps réel.

```bash
# Lancer le dashboard
python tools/mock_exchange/serve_exchange.py

# Ouvrir dans le navigateur
open http://localhost:5557
```

### Fonctionnalités du Dashboard

- **🎰 Sélecteur de Scénarios** : Choisir parmi 9 scénarios de marché (bull run, crash, volatile, etc.)
- **⚙️ Configuration** : Ajuster le prix initial, volatilité, spread
- **▶️ Contrôles** : Start, Pause, Stop des simulations
- **📊 Statistiques en temps réel** :
    - Prix actuel avec formatage
    - Retour total (%) avec coloration (vert/rouge)
    - Prix min/max atteints
    - Volatilité calculée
    - Nombre de candles générées
- **📈 Graphique Live** : Chart.js affichant les 50 derniers prix
- **🔄 Auto-refresh** : Mise à jour toutes les 500ms
- **🎨 Design unifié** : Même charte graphique que les autres outils

### API REST

Le dashboard expose une API REST pour intégration programmatique :

```python
import requests

# Démarrer une simulation
response = requests.post('http://localhost:5557/api/start', json={
    'scenario': 'flash_crash',
    'initial_price': 50000.0,
    'volatility_multiplier': 1.0,
    'spread_bps': 20
})
sim_id = response.json()['simulation_id']

# Obtenir les statistiques
stats = requests.get(f'http://localhost:5557/api/stats/{sim_id}').json()
print(f"Current price: ${stats['current_price']:,.2f}")
print(f"Total return: {stats['total_return_pct']:.2f}%")

# Pause
requests.post(f'http://localhost:5557/api/pause/{sim_id}')

# Stop
requests.post(f'http://localhost:5557/api/stop/{sim_id}')
```

### Intégration

- **Port** : 5557
- **Liens** : Navigation vers Event Flow (5555), Recorder (5556), Testing (5558)
- **Tests** : `tests/tools/test_serve_exchange.py` (8 tests passing)

---

## 🚀 Usage Rapide

### Utilisation Basique

```python
from tools.mock_exchange.scenario_exchange import ScenarioBasedMockExchange, MarketScenario

# Créer un exchange avec scénario bull run
exchange = ScenarioBasedMockExchange(
    scenario=MarketScenario.BULL_RUN,
    initial_price=50000.0,
    pair="BTC/USDT"
)

# Fetch current price
price_data = exchange.fetch_current_price()

print(f"Price: ${price_data.current_price.price:,.2f}")
print(f"Buy:   ${price_data.buy_price.price:,.2f}")
print(f"Sell:  ${price_data.sell_price.price:,.2f}")
print(f"Candles: {len(price_data.candlesticks)} OHLCV rows")
```

### Dans les Tests Pytest

```python
import pytest
from tools.mock_exchange.scenario_exchange import ScenarioBasedMockExchange, MarketScenario


@pytest.mark.parametrize("scenario", [
    MarketScenario.BULL_RUN,
    MarketScenario.BEAR_CRASH,
    MarketScenario.FLASH_CRASH
])
def test_bot_behavior_in_scenario(scenario):
    """Test bot behavior across different market conditions"""
    exchange = ScenarioBasedMockExchange(scenario=scenario)

    # Run your bot with this exchange
    bot = TradingBot(exchange=exchange)
    bot.run_for_n_cycles(50)

    # Assert expected behavior
    assert bot.total_return > -20  # Never lose more than 20%
```

### Avec EventRecorder

```python
from tools.event_recorder.event_recorder import EventRecorder
from tools.mock_exchange.scenario_exchange import ScenarioBasedMockExchange, MarketScenario

# Combine scenario testing with event recording
exchange = ScenarioBasedMockExchange(scenario=MarketScenario.FLASH_CRASH)
recorder = EventRecorder("flash_crash_test")

recorder.start_recording(service_bus)

# Run bot with scenario
for _ in range(50):
    price_data = exchange.fetch_current_price()
    # ... bot processes price ...

recorder.save()

# Later, replay to reproduce exact behavior
```

## 🎛️ Paramètres de Configuration

```python
exchange = ScenarioBasedMockExchange(
    scenario=MarketScenario.VOLATILE,  # Scénario de marché
    initial_price=50000.0,  # Prix de départ
    pair="BTC/USDT",  # Paire de trading
    candle_count=100,  # Nombre de candles historiques
    volatility_multiplier=2.0,  # Multiplicateur de volatilité (défaut: 1.0)
    spread_bps=20  # Spread en basis points (défaut: 20 = 0.2%)
)
```

### Exemples de Configuration

```python
# Haute volatilité pour stress testing
exchange = ScenarioBasedMockExchange(
    scenario=MarketScenario.VOLATILE,
    volatility_multiplier=3.0
)

# Spread élevé (comme sur des exchanges exotiques)
exchange = ScenarioBasedMockExchange(
    scenario=MarketScenario.SIDEWAYS,
    spread_bps=100  # 1% spread
)

# Beaucoup de données historiques
exchange = ScenarioBasedMockExchange(
    scenario=MarketScenario.BULL_RUN,
    candle_count=500
)
```

## 📊 Statistiques et Analyse

```python
exchange = ScenarioBasedMockExchange(scenario=MarketScenario.PUMP_AND_DUMP)

# Simulate 100 candles
for _ in range(100):
    exchange.fetch_current_price()

# Get statistics
stats = exchange.get_price_statistics()

print(f"Min Price:       ${stats['min_price']:,.2f}")
print(f"Max Price:       ${stats['max_price']:,.2f}")
print(f"Mean Price:      ${stats['mean_price']:,.2f}")
print(f"Volatility:      {stats['volatility']:.4f}")
print(f"Total Return:    {stats['total_return_pct']:+.2f}%")
print(f"Calls:           {stats['call_count']}")
```

## 🔍 Cas d'Usage Avancés

### 1. Tester la Robustesse avec Flash Crash

```python
def test_bot_survives_flash_crash():
    """Ensure bot doesn't panic sell during flash crash"""
    exchange = ScenarioBasedMockExchange(scenario=MarketScenario.FLASH_CRASH)
    bot = TradingBot(exchange=exchange)

    # Before crash
    for _ in range(15):
        bot.tick()

    initial_positions = len(bot.positions)

    # During crash (candles 20-30)
    for _ in range(15):
        bot.tick()

    # Bot should NOT have panic-sold
    assert len(bot.positions) >= initial_positions
```

### 2. Détecter les Candles Irréguliers

```python
def test_bot_handles_irregular_candles():
    """Ensure bot handles irregular timestamp intervals gracefully"""
    exchange = ScenarioBasedMockExchange(
        scenario=MarketScenario.IRREGULAR_CANDLES
    )

    bot = TradingBot(exchange=exchange)

    # Should raise CandleIntervalError and recover
    with pytest.raises(CandleIntervalError):
        for _ in range(20):
            bot.tick()
```

### 3. Comparer les Stratégies

```python
def compare_strategies_across_scenarios():
    """Compare different strategies across market conditions"""
    strategies = [AggressiveStrategy(), ConservativeStrategy()]
    scenarios = [MarketScenario.BULL_RUN, MarketScenario.BEAR_CRASH]

    results = {}

    for strategy in strategies:
        for scenario in scenarios:
            exchange = ScenarioBasedMockExchange(scenario=scenario)
            bot = TradingBot(strategy=strategy, exchange=exchange)

            for _ in range(100):
                bot.tick()

            results[(strategy.name, scenario.value)] = bot.total_return

    # Analyze which strategy performs best in each scenario
    print(results)
```

### 4. Stress Testing avec Haute Volatilité

```python
def test_bot_under_extreme_volatility():
    """Test bot behavior under extreme market conditions"""
    exchange = ScenarioBasedMockExchange(
        scenario=MarketScenario.VOLATILE,
        volatility_multiplier=5.0  # 5x normal volatility!
    )

    bot = TradingBot(exchange=exchange)

    for _ in range(100):
        bot.tick()

    # Bot should survive without catastrophic loss
    assert bot.capital > bot.initial_capital * 0.5  # Max 50% loss
```

### 5. Test de Régression avec Reset

```python
def test_strategy_consistency():
    """Ensure strategy produces consistent results"""
    exchange = ScenarioBasedMockExchange(scenario=MarketScenario.BULL_RUN)

    # Run 1
    bot1 = TradingBot(exchange=exchange, random_seed=42)
    for _ in range(50):
        bot1.tick()
    result1 = bot1.total_return

    # Reset exchange
    exchange.reset()

    # Run 2
    bot2 = TradingBot(exchange=exchange, random_seed=42)
    for _ in range(50):
        bot2.tick()
    result2 = bot2.total_return

    # Should be identical (if bot is deterministic)
    assert result1 == result2
```

## 🧪 Tests

Tests disponibles dans `tests/tools/test_scenario_exchange.py` :

```bash
# Lancer tous les tests
python -m pytest tests/tools/test_scenario_exchange.py -v

# Tester un scénario spécifique
python -m pytest tests/tools/test_scenario_exchange.py::TestBullRunScenario -v

# Tester les scénarios avancés
python -m pytest tests/tools/test_scenario_exchange.py::TestAdvancedScenarios -v
```

**Résultats** : ✅ 18/18 tests passent

## 📝 Exemples

Voir `example_scenarios.py` pour des exemples complets :

```bash
python tools/mock_exchange/example_scenarios.py
```

### CLI Interface

```bash
# Simuler un bull run
python tools/mock_exchange/scenario_exchange.py --scenario bull_run --calls 100

# Simuler un flash crash
python tools/mock_exchange/scenario_exchange.py --scenario flash_crash --calls 50 --initial-price 60000

# Voir toutes les options
python tools/mock_exchange/scenario_exchange.py --help
```

## 🎨 Personnalisation

### Créer un Nouveau Scénario

Pour ajouter un nouveau scénario :

1. Ajouter à l'enum `MarketScenario`
2. Implémenter la logique dans `_generate_next_price()`
3. Ajouter des tests dans `test_scenario_exchange.py`

Exemple :

```python
class MarketScenario(Enum):
    # ... existing scenarios ...
    MOON_SHOT = "moon_shot"  # Nouveau scénario


def _generate_next_price(self) -> float:
    # ... existing logic ...
    elif self.scenario == MarketScenario.MOON_SHOT:
    # Exponential growth: +100% in 50 candles
    return self.current_price * 1.02  # ~2% per candle
```

## 🔧 Détails Techniques

### Structure de MarketPriceData

```python
@dataclass
class MarketPriceData:
    current_price: Price  # Prix actuel
    buy_price: Price  # Prix d'achat (avec spread)
    sell_price: Price  # Prix de vente (avec spread)
    candlesticks: DataFrame  # OHLCV historique
    timestamp: str  # ISO 8601 timestamp
```

### Format des Candles

```python
candlesticks = pd.DataFrame({
    'timestamp': [1697234500000, ...],  # Unix timestamp en ms
    'open': [50000.0, ...],
    'high': [50200.0, ...],
    'low': [49800.0, ...],
    'close': [50100.0, ...],
    'volume': [123.45, ...]
})
```

### Logique OHLC

Les candles respectent toujours :

- `high >= max(open, close, low)`
- `low <= min(open, close, high)`
- Volume corrélé à la volatilité

## 🎯 Best Practices

1. **Tests Paramétrés** : Utilisez `@pytest.mark.parametrize` pour tester tous les scénarios
2. **Combinaison avec EventRecorder** : Enregistrez les scénarios problématiques pour rejeu
3. **Ajuster la Volatilité** : Utilisez `volatility_multiplier` pour stress testing
4. **Reset Entre Tests** : Appelez `exchange.reset()` pour réutiliser la même instance
5. **Vérifier les Statistiques** : Utilisez `get_price_statistics()` pour valider les résultats
6. **CLI pour Debug** : Utilisez l'interface CLI pour visualiser rapidement un scénario

## ⚠️ Limitations

- Les prix sont générés algorithmiquement (pas de données réelles historiques)
- La corrélation volume/prix est simplifiée
- Les gaps dans IRREGULAR_CANDLES sont prédéfinis (tous les 10 candles)
- Le spread est constant (pas de simulation d'order book)

## 🚧 Extensions Futures

Idées pour améliorer :

- Support de données historiques réelles (CSV, API)
- Simulation d'order book avec profondeur
- Événements aléatoires (exchange downtime, etc.)
- Corrélations entre plusieurs paires
- Latence réseau simulée

## 📚 Voir Aussi

- **Event Recorder** : `tools/event_recorder/` - Pour enregistrer les sessions
- **Event Flow** : `tools/event_flow/` - Pour visualiser les événements
- **Tests Integration** : `tests/integration/` - Tests avec mock exchange

---

**Status** : ✅ Production-ready
**Tests** : ✅ 18/18 passing
**Documentation** : ✅ Complete
