# 📊 Event Metrics Collector

Système de collecte et d'analyse de métriques pour les événements.

## 🎯 Vue d'ensemble

Le **Event Metrics Collector** fournit un système de collecte de métriques simple mais puissant pour monitorer les événements dans vos architectures event-driven. Il
permet de :

- ✅ Compter les événements publiés/traités/échoués
- ✅ Mesurer les temps de traitement (P50, P95, P99)
- ✅ Calculer les taux d'erreur
- ✅ Identifier les événements les plus fréquents
- ✅ Profiler les handlers
- ✅ Exporter les métriques

## 🚀 Quick Start

### Installation

Le module metrics est inclus dans `python-pubsub-devtools` :

```bash
pip install python-pubsub-devtools
```

### Usage basique

```python
from python_pubsub_devtools.metrics import get_metrics_collector, collect_metrics

# Obtenir le collecteur global
collector = get_metrics_collector()

# Enregistrer un événement publié
collector.record_event_published('OrderCreated')

# Enregistrer un événement traité avec durée
collector.record_event_processed('OrderCreated', duration_ms=15.5)

# Enregistrer un événement en échec
collector.record_event_failed('PaymentFailed', duration_ms=25.0)

# Obtenir le résumé
summary = collector.get_summary()
print(f"Total events: {summary['total_events']}")
print(f"Error rate: {summary['error_rate']:.2f}%")
```

### Décorateur automatique

Le plus simple est d'utiliser le décorateur `@collect_metrics` qui enregistre automatiquement toutes les métriques :

```python
from python_pubsub_devtools.metrics import collect_metrics

@collect_metrics
def handle_order(event):
    """Handler avec collecte automatique de métriques"""
    process_order(event)
    return "Order processed"

# Les métriques sont automatiquement collectées :
# - Nombre d'exécutions
# - Durée d'exécution
# - Succès/échecs
```

## 📖 Usage détaillé

### 1. Collecteur de métriques

```python
from python_pubsub_devtools.metrics import EventMetricsCollector

# Créer un collecteur
collector = EventMetricsCollector()

# Enregistrer différents types d'événements
collector.record_event_published('OrderCreated')
collector.record_event_processed('OrderCreated', 10.5)
collector.record_event_failed('PaymentFailed', 50.0)

# Enregistrer l'exécution d'un handler
collector.record_handler_execution(
    handler_name='handle_order',
    event_name='OrderCreated',
    duration_ms=15.0,
    success=True
)
```

### 2. Obtenir les statistiques

#### Résumé global

```python
summary = collector.get_summary()

# Résultat :
{
    'total_events': 1250,
    'total_processed': 1200,
    'total_failed': 50,
    'error_rate': 4.0,
    'avg_processing_time_ms': 12.5,
    'event_rate_per_sec': 20.8,
    'top_events': [
        {'event_type': 'OrderCreated', 'count': 500},
        {'event_type': 'PaymentProcessing', 'count': 300},
        ...
    ],
    'uptime_seconds': 3600.0,
    'start_time': '2025-10-13T10:00:00'
}
```

#### Statistiques par événement

```python
stats = collector.get_event_stats('OrderCreated')

# Résultat :
{
    'event_type': 'OrderCreated',
    'published': 500,
    'processed': 490,
    'failed': 10,
    'error_rate': 2.0,
    'processing_time': {
        'count': 490,
        'min': 5.2,
        'max': 50.8,
        'avg': 15.3,
        'p50': 12.5,
        'p95': 35.2,
        'p99': 45.1
    }
}
```

#### Statistiques par handler

```python
stats = collector.get_handler_stats('handle_order')

# Résultat :
{
    'handler': 'handle_order',
    'executions': 500,
    'avg_duration_ms': 15.3,
    'min_duration_ms': 5.2,
    'max_duration_ms': 50.8
}
```

### 3. Réinitialiser les métriques

```python
# Réinitialiser toutes les métriques
collector.reset()
```

## 💻 CLI - Interface en ligne de commande

Le CLI permet de visualiser les métriques directement depuis le terminal.

### Afficher le résumé

```bash
# Résumé complet
$ pubsub-tools metrics show

================================================================================
                          📊 Event Metrics Summary
================================================================================

Overall Statistics:
  Total Events Published:  1,250
  Total Events Processed:  1,200
  Total Events Failed:     50
  Error Rate:              4.00%
  Avg Processing Time:     12.50 ms
  Event Rate:              20.83 events/sec
  Uptime:                  1.0h
  Start Time:              2025-10-13T10:00:00

Top Events:
+---------------------+-------+------------+
| Event Type          | Count | Percentage |
+---------------------+-------+------------+
| OrderCreated        | 500   | 40.0%      |
| PaymentProcessing   | 300   | 24.0%      |
| OrderShipped        | 200   | 16.0%      |
+---------------------+-------+------------+

================================================================================
```

### Format JSON

```bash
$ pubsub-tools metrics show --format json

{
  "total_events": 1250,
  "total_processed": 1200,
  "total_failed": 50,
  "error_rate": 4.0,
  ...
}
```

### Statistiques d'un événement spécifique

```bash
$ pubsub-tools metrics event OrderCreated

================================================================================
                       📊 Statistics for: OrderCreated
================================================================================

  Published:   500
  Processed:   490
  Failed:      10
  Error Rate:  2.00%

Processing Time:
  Count:   490
  Min:     5.20 ms
  Max:     50.80 ms
  Avg:     15.30 ms
  P50:     12.50 ms
  P95:     35.20 ms
  P99:     45.10 ms

================================================================================
```

### Statistiques d'un handler

```bash
$ pubsub-tools metrics handler handle_order

================================================================================
                  📊 Statistics for handler: handle_order
================================================================================

  Executions:       500
  Avg Duration:     15.30 ms
  Min Duration:     5.20 ms
  Max Duration:     50.80 ms

================================================================================
```

### Lister tous les événements

```bash
$ pubsub-tools metrics list

================================================================================
                         📋 Recorded Event Types
================================================================================

+------------------------+-------+
| Event Type             | Count |
+------------------------+-------+
| OrderCreated           | 500   |
| PaymentProcessing      | 300   |
| OrderShipped           | 200   |
| OrderCancelled         | 150   |
| NotificationSent       | 100   |
+------------------------+-------+

Total: 5 event types
================================================================================
```

### Exporter les métriques

```bash
$ pubsub-tools metrics export metrics.json
✅ Metrics exported to: metrics.json

$ pubsub-tools metrics export metrics.json --format json
✅ Metrics exported to: metrics.json
```

### Réinitialiser les métriques

```bash
$ pubsub-tools metrics reset --confirm
✅ All metrics have been reset.
```

## 🎓 Exemples d'usage

### Exemple 1 : E-Commerce Order Processing

```python
from python_pubsub_devtools.metrics import collect_metrics, get_metrics_collector

@collect_metrics
def handle_order_created(event):
    """Process new order"""
    order = create_order(event.data)
    charge_payment(order)
    send_confirmation_email(order)
    return order

@collect_metrics
def handle_payment_failed(event):
    """Handle payment failure"""
    cancel_order(event.order_id)
    notify_customer(event.customer_id)

# Après traitement de 1000 commandes
collector = get_metrics_collector()
summary = collector.get_summary()

print(f"Orders processed: {summary['total_processed']}")
print(f"Payment failures: {summary['total_failed']}")
print(f"Success rate: {100 - summary['error_rate']:.2f}%")
```

### Exemple 2 : Monitoring High-Frequency Trading

```python
from python_pubsub_devtools.metrics import EventMetricsCollector

collector = EventMetricsCollector()

# Trading loop
while trading_active:
    tick = exchange.get_market_tick()

    start = time.time()
    collector.record_event_published('MarketTick')

    # Process tick
    analyze_market(tick)
    execute_trades(tick)

    duration = (time.time() - start) * 1000
    collector.record_event_processed('MarketTick', duration)

# Check performance
stats = collector.get_event_stats('MarketTick')
print(f"Ticks processed: {stats['processed']}")
print(f"Avg latency: {stats['processing_time']['avg']:.2f}ms")
print(f"P99 latency: {stats['processing_time']['p99']:.2f}ms")
```

### Exemple 3 : Microservices avec Event Bus

```python
from python_pubsub_devtools.metrics import collect_metrics, get_metrics_collector

class OrderService:
    @collect_metrics
    async def handle_order_created(self, event):
        """Order service handler"""
        await self.validate_order(event)
        await self.reserve_inventory(event)
        await self.create_order(event)

class PaymentService:
    @collect_metrics
    async def handle_payment_required(self, event):
        """Payment service handler"""
        await self.charge_card(event)
        await self.emit_payment_completed(event)

class NotificationService:
    @collect_metrics
    async def handle_order_confirmed(self, event):
        """Notification service handler"""
        await self.send_email(event)
        await self.send_sms(event)

# Monitoring
collector = get_metrics_collector()

# Per-service stats
order_stats = collector.get_handler_stats('handle_order_created')
payment_stats = collector.get_handler_stats('handle_payment_required')
notif_stats = collector.get_handler_stats('handle_order_confirmed')

print(f"Order Service: {order_stats['executions']} executions, "
      f"{order_stats['avg_duration_ms']:.2f}ms avg")
print(f"Payment Service: {payment_stats['executions']} executions, "
      f"{payment_stats['avg_duration_ms']:.2f}ms avg")
print(f"Notification Service: {notif_stats['executions']} executions, "
      f"{notif_stats['avg_duration_ms']:.2f}ms avg")
```

### Exemple 4 : Chaos Engineering & Testing

```python
from python_pubsub_devtools.metrics import EventMetricsCollector

collector = EventMetricsCollector()

# Test avec injection de chaos
chaos_injector.inject_latency(handler='handle_payment', latency_ms=500)

# Execute test scenario
for i in range(100):
    event = OrderCreated(order_id=f"order-{i}")

    try:
        start = time.time()
        handle_order(event)
        duration = (time.time() - start) * 1000
        collector.record_event_processed('OrderCreated', duration)
    except Exception as e:
        collector.record_event_failed('OrderCreated')

# Analyze impact
stats = collector.get_event_stats('OrderCreated')
print(f"Success rate under chaos: {100 - stats['error_rate']:.2f}%")
print(f"P95 latency with injected delay: {stats['processing_time']['p95']:.2f}ms")
```

## 🔧 API Reference

### EventMetricsCollector

#### Méthodes principales

```python
class EventMetricsCollector:
    def record_event_published(self, event_name: str) -> None:
        """Enregistrer un événement publié"""

    def record_event_processed(self, event_name: str, duration_ms: float) -> None:
        """Enregistrer un événement traité avec durée"""

    def record_event_failed(self, event_name: str, duration_ms: Optional[float] = None) -> None:
        """Enregistrer un événement en échec"""

    def record_handler_execution(
        self,
        handler_name: str,
        event_name: str,
        duration_ms: float,
        success: bool = True
    ) -> None:
        """Enregistrer l'exécution d'un handler"""

    def get_summary(self) -> Dict[str, Any]:
        """Obtenir le résumé complet des métriques"""

    def get_event_stats(self, event_name: str) -> Optional[Dict[str, Any]]:
        """Obtenir les statistiques pour un événement"""

    def get_handler_stats(self, handler_name: str) -> Dict[str, Any]:
        """Obtenir les statistiques pour un handler"""

    def get_event_rate(self, window_seconds: int = 60) -> float:
        """Calculer le taux d'événements sur une fenêtre"""

    def reset(self) -> None:
        """Réinitialiser toutes les métriques"""
```

### Décorateur collect_metrics

```python
@collect_metrics
def handler(event):
    """
    Décorateur qui collecte automatiquement :
    - Nombre d'exécutions
    - Durée d'exécution
    - Succès/échecs

    Compatible avec fonctions sync et async.
    """
    pass
```

### Fonctions utilitaires

```python
def get_metrics_collector() -> EventMetricsCollector:
    """Obtenir l'instance globale du collecteur"""
    pass
```

## 📊 Métriques collectées

### Compteurs

- **events_published**: Nombre d'événements publiés par type
- **events_processed**: Nombre d'événements traités avec succès
- **events_failed**: Nombre d'événements en échec

### Histogrammes

- **processing_time**: Distribution des temps de traitement
    - Min, Max, Avg
    - P50 (médiane), P95, P99
- **handler_execution**: Distribution des temps d'exécution des handlers

### Métriques calculées

- **error_rate**: Taux d'erreur global (%)
- **event_rate**: Taux d'événements par seconde
- **uptime**: Durée depuis le démarrage

## 🎯 Best Practices

### 1. Utiliser le décorateur pour handlers

```python
# ✅ Bon : Décorateur automatique
@collect_metrics
def handle_order(event):
    process_order(event)

# ❌ Moins bon : Enregistrement manuel
def handle_order(event):
    collector = get_metrics_collector()
    start = time.time()
    try:
        process_order(event)
        collector.record_event_processed('OrderCreated', (time.time() - start) * 1000)
    except Exception as e:
        collector.record_event_failed('OrderCreated')
        raise
```

### 2. Monitorer les événements critiques

```python
# Événements à fort impact business
@collect_metrics
def handle_payment(event):
    charge_customer(event)

# Vérifier régulièrement
stats = collector.get_event_stats('PaymentProcessing')
if stats['error_rate'] > 5.0:
    alert_team("Payment error rate too high!")
```

### 3. Exporter pour analyse

```bash
# Export périodique pour analyse historique
$ pubsub-tools metrics export metrics-$(date +%Y%m%d-%H%M%S).json
```

### 4. Réinitialiser entre tests

```python
# Dans vos tests
def setUp(self):
    collector = get_metrics_collector()
    collector.reset()
```

## 🚀 Prochaines étapes

Les métriques sont la **première étape** vers l'observabilité complète. Prochaines améliorations :

1. **Integration Prometheus** : Export des métriques au format Prometheus
2. **Alerting** : Alertes automatiques sur seuils
3. **Dashboard Web** : Visualisation temps réel
4. **Distributed Tracing** : Corrélation d'événements
5. **Grafana Dashboards** : Dashboards préconfigurés

Voir [04_ROADMAP.md](./04_ROADMAP.md) pour plus de détails.

## 📚 Références

- [05_QUICK_WINS.md](./05_QUICK_WINS.md) - Autres améliorations rapides
- [01_ARCHITECTURE.md](./01_ARCHITECTURE.md) - Architecture du système
- [02_USE_CASES.md](./02_USE_CASES.md) - Cas d'usage complets

---

**Version**: 1.0.0
**Last Updated**: 2025-10-13
