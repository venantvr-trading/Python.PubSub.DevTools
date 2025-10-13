# 💼 Use Cases - Cas d'Usage Réels

Exemples concrets d'utilisation de PubSub DevTools dans des contextes professionnels.

---

## 🏪 E-Commerce Platform

### Contexte
Plateforme e-commerce avec microservices : Orders, Payments, Inventory, Shipping, Notifications.

### Problématiques
- **Debugging** : Un client dit qu'il n'a pas reçu de confirmation de commande
- **Testing** : Tester le flow complet de commande sans environnement de production
- **Monitoring** : Surveiller les performances et détecter les goulots d'étranglement

### Solution avec PubSub DevTools

#### 1. Tracer un Order Flow Complet

```bash
# Enregistrer tous les événements pour une commande spécifique
$ pubsub-tools recorder start --filter "order_id:ORD-12345"

# Le client passe une commande
# ... events flowing ...

$ pubsub-tools recorder stop --output order_12345_flow.json
```

**Analyse du flow** :
```bash
$ pubsub-tools flow analyze order_12345_flow.json

📊 Flow Analysis for order_id:ORD-12345
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ OrderCreated (0ms)
  └→ PaymentService (2.3ms)
      ✅ PaymentProcessing (15ms)
         └→ PaymentGateway (1250ms) ⚠️  SLOW
            ✅ PaymentCompleted (8ms)
               └→ InventoryService (5ms)
                  ✅ InventoryReserved (23ms)
                     └→ ShippingService (12ms)
                        ✅ ShippingLabelCreated (45ms)
                           └→ NotificationService (3ms)
                              ❌ EmailNotificationFailed ⚠️  ERROR
                                 Error: SMTP timeout

🔍 Issues Found:
  1. PaymentGateway slow (1250ms > 100ms threshold)
  2. EmailNotificationFailed - SMTP timeout
  3. CustomerNotification never sent

💡 Recommendations:
  - Add timeout to PaymentGateway call
  - Implement retry for email notifications
  - Add DLQ for failed notifications
```

#### 2. Tester le Flow de Commande

```python
# tests/test_order_flow.py
import pytest
from pubsub_devtools.testing import ScenarioTester, assert_event_published

@pytest.fixture
def order_scenario():
    return ScenarioTester.from_yaml("scenarios/order_flow.yaml")

def test_successful_order_flow(order_scenario):
    """Test le flow complet d'une commande réussie"""

    # Execute scenario
    result = order_scenario.run()

    # Assertions
    assert_event_published(result, "OrderCreated", count=1)
    assert_event_published(result, "PaymentCompleted", count=1)
    assert_event_published(result, "InventoryReserved", count=1)
    assert_event_published(result, "ShippingLabelCreated", count=1)
    assert_event_published(result, "CustomerNotified", count=1)

    # Verify timing
    assert result.total_duration_ms < 5000  # Max 5 secondes

    # Verify order
    assert result.event_order == [
        "OrderCreated",
        "PaymentProcessing",
        "PaymentCompleted",
        "InventoryReserved",
        "ShippingLabelCreated",
        "CustomerNotified"
    ]
```

**Scenario YAML** :
```yaml
# scenarios/order_flow.yaml
name: "Order Flow - Happy Path"
description: "Complete order flow from creation to notification"

setup:
  services:
    - order_service
    - payment_service
    - inventory_service
    - shipping_service
    - notification_service

steps:
  - trigger:
      event: OrderCreated
      data:
        order_id: "ORD-TEST-001"
        customer_id: "CUST-123"
        items:
          - product_id: "PROD-456"
            quantity: 2
            price: 29.99

  - wait_for_event:
      event: PaymentCompleted
      timeout_seconds: 30

  - assert:
      event_count:
        PaymentCompleted: {exact: 1}
        InventoryReserved: {exact: 1}
        ShippingLabelCreated: {exact: 1}
        CustomerNotified: {exact: 1}

  - assert:
      event_data:
        CustomerNotified:
          - field: "order_id"
            value: "ORD-TEST-001"
          - field: "status"
            value: "confirmed"
```

#### 3. Chaos Testing - Payment Gateway Failure

```yaml
# scenarios/order_flow_payment_failure.yaml
name: "Order Flow - Payment Gateway Failure"

chaos:
  - type: inject_failure
    event: PaymentProcessing
    at_cycle: 1
    error_message: "Payment gateway timeout"

steps:
  - trigger:
      event: OrderCreated

  - wait_for_event:
      event: PaymentFailed
      timeout_seconds: 30

  - assert:
      event_count:
        PaymentFailed: {exact: 1}
        OrderCancelled: {exact: 1}
        InventoryReleased: {exact: 1}  # Saga compensation
```

---

## 🏦 Banking - Fraud Detection System

### Contexte
Système de détection de fraude temps réel pour transactions bancaires.

### Problématiques
- **Performance critique** : Décisions en < 100ms
- **Faux positifs** : Éviter de bloquer transactions légitimes
- **Audit** : Traçabilité complète pour régulation

### Solution avec PubSub DevTools

#### 1. Performance Monitoring

```python
# services/fraud_detection.py
from pubsub_devtools.observability import monitor_performance

@monitor_performance(
    slo_ms=100,  # SLO: < 100ms
    alert_on_breach=True
)
@event_handler("TransactionInitiated")
async def check_fraud(event: TransactionInitiated):
    """Check transaction for fraud"""

    # Check rules
    risk_score = await fraud_engine.calculate_risk(event)

    if risk_score > 0.8:
        await event_bus.publish(TransactionBlocked(
            transaction_id=event.transaction_id,
            reason="High fraud risk",
            risk_score=risk_score
        ))
    else:
        await event_bus.publish(TransactionApproved(
            transaction_id=event.transaction_id,
            risk_score=risk_score
        ))
```

**Dashboard automatique** :
```bash
$ pubsub-tools dashboard start --service fraud-detection

📊 Fraud Detection Dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Performance Metrics (last 1h):
  ✅ Avg latency: 45ms (SLO: < 100ms)
  ✅ P95 latency: 78ms
  ⚠️  P99 latency: 105ms (breaching SLO!)

  Throughput: 1,245 transactions/minute
  Error rate: 0.02%

Fraud Detection:
  Blocked: 23 transactions (1.8%)
  Approved: 1,222 transactions
  False positives: 2 (reported by customers)

⚠️  Alerts:
  - P99 latency breaching SLO (last 15 min)
  - Spike in blocked transactions from IP 123.45.67.89
```

#### 2. Audit Trail Complet

```python
# Audit automatique
from pubsub_devtools.audit import AuditLogger

audit = AuditLogger(
    storage="postgresql",
    retention_days=2555  # 7 years for compliance
)

# Auto-log tous les événements fraud-related
audit.enable_auto_logging(
    event_types=["TransactionInitiated", "TransactionBlocked", "TransactionApproved"],
    include_sensitive_data=False,  # Mask PII
    encryption=True
)
```

**Query audit trail** :
```bash
$ pubsub-tools audit query \
    --transaction-id TXN-123456 \
    --format compliance-report

Compliance Report: TXN-123456
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Transaction ID: TXN-123456
Customer ID: [REDACTED]
Amount: $5,000.00
Timestamp: 2025-10-13 14:35:22 UTC

Event Chain:
  1. 14:35:22.123 TransactionInitiated
     Source: mobile-app
     IP: 192.168.1.100
     Device: iPhone 13 Pro

  2. 14:35:22.145 FraudCheckStarted
     Handler: fraud-detection-v2.3.1
     Rules evaluated: 47

  3. 14:35:22.187 RiskScoreCalculated
     Score: 0.23 (Low Risk)
     Factors: location_match, amount_within_profile

  4. 14:35:22.195 TransactionApproved
     Approved by: fraud-detection-service
     Confidence: 98.5%

Total processing time: 72ms
Decision: APPROVED
Signature: [SHA256 hash]
```

---

## 📱 Social Media Platform - Notification System

### Contexte
Plateforme sociale avec système de notifications (likes, comments, mentions, etc.).

### Problématiques
- **Volume élevé** : Millions de notifications/jour
- **Rate limiting** : Ne pas spammer les users
- **Prioritization** : Notifications importantes en premier

### Solution avec PubSub DevTools

#### 1. Rate Limiting Intelligent

```python
# services/notification_service.py
from pubsub_devtools.reliability import RateLimiter

# Rate limit par user
@rate_limit(
    strategy="sliding_window",
    max_per_user=10,
    window_minutes=60,
    priority_boost=True  # Allow important notifications
)
@event_handler("NotificationTriggered")
async def send_notification(event: NotificationTriggered):
    """Send notification with rate limiting"""

    # Check priority
    if event.priority == "urgent":
        # Bypass rate limit for urgent notifications
        await notification_sender.send_immediately(event)
    else:
        # Normal flow with rate limiting
        await notification_sender.send(event)
```

#### 2. Batch Processing pour Performance

```python
# Batch notifications for efficiency
@batch_handler(
    batch_size=100,
    max_wait_ms=5000,
    flush_on_idle=True
)
@event_handler("LikeReceived")
async def process_like_notifications(events: List[LikeReceived]):
    """Process likes in batches"""

    # Group by user
    by_user = defaultdict(list)
    for event in events:
        by_user[event.user_id].append(event)

    # Send aggregated notifications
    for user_id, likes in by_user.items():
        if len(likes) == 1:
            await send_notification(
                user_id,
                f"{likes[0].liker_name} liked your post"
            )
        else:
            await send_notification(
                user_id,
                f"{likes[0].liker_name} and {len(likes)-1} others liked your post"
            )
```

**Metrics** :
```bash
$ pubsub-tools metrics show --service notification

📊 Notification Service Metrics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Throughput (last 1h):
  Total notifications: 1,245,234
  Rate: 347 notifications/sec
  Peak rate: 1,203 notifications/sec (15:34)

Batching Efficiency:
  Avg batch size: 47 notifications
  Batching saved: 95.2% DB queries

Rate Limiting:
  Users rate-limited: 2,341 (0.2%)
  Notifications dropped: 8,723 (0.7%)
  Urgent notifications bypassed: 1,234

Delivery:
  Push: 89.2% (delivered)
  Email: 95.8% (delivered)
  SMS: 97.3% (delivered)
  Failed: 2.1% → DLQ
```

---

## 🚗 Ride-Sharing App - Real-time Matching

### Contexte
App de covoiturage avec matching temps réel drivers/riders.

### Problématiques
- **Latence critique** : Match en < 3 secondes
- **Geo-distributed** : Events dans multiple régions
- **Complex saga** : Booking → Accept → Navigate → Complete

### Solution avec PubSub DevTools

#### 1. Saga Orchestration pour Booking

```python
# services/booking_saga.py
from pubsub_devtools.patterns import Saga

@saga("BookingFlowSaga")
class BookingFlowSaga:
    """Orchestrate booking flow with compensation"""

    @step(compensating_action="cancel_match")
    async def match_driver(self, event: RideRequested):
        """Find available driver"""
        driver = await matching_service.find_driver(
            location=event.pickup_location,
            radius_km=5
        )

        if not driver:
            raise NoDriverAvailableError()

        return DriverMatched(
            booking_id=event.booking_id,
            driver_id=driver.id,
            eta_minutes=driver.eta
        )

    @step(compensating_action="release_driver")
    async def wait_for_acceptance(self, event: DriverMatched):
        """Wait for driver acceptance"""
        # Timeout after 30 seconds
        accepted = await wait_for_event(
            "DriverAccepted",
            timeout=30,
            filter={"booking_id": event.booking_id}
        )

        if not accepted:
            raise DriverDidNotAcceptError()

        return DriverAccepted(booking_id=event.booking_id)

    @step(compensating_action="cancel_trip")
    async def start_trip(self, event: DriverAccepted):
        """Start the trip"""
        return TripStarted(booking_id=event.booking_id)

    # Compensation actions
    async def cancel_match(self, event, error):
        await event_bus.publish(MatchCancelled(booking_id=event.booking_id))

    async def release_driver(self, event, error):
        await event_bus.publish(DriverReleased(
            driver_id=event.driver_id,
            reason="No acceptance"
        ))

    async def cancel_trip(self, event, error):
        await event_bus.publish(TripCancelled(
            booking_id=event.booking_id,
            reason=str(error)
        ))
```

#### 2. Testing Saga with Failures

```yaml
# scenarios/booking_saga_driver_no_accept.yaml
name: "Booking Saga - Driver Doesn't Accept"

steps:
  - trigger:
      event: RideRequested
      data:
        booking_id: "BOOK-001"
        pickup_location: {lat: 48.8566, lon: 2.3522}

  - wait_for_event:
      event: DriverMatched
      timeout_seconds: 10

  - wait_for_time: 31  # Wait > 30s timeout

  - assert:
      event_count:
        DriverMatched: {exact: 1}
        DriverReleased: {exact: 1}  # Compensation
        MatchCancelled: {exact: 1}  # Compensation
        RideRequestFailed: {exact: 1}

  - assert:
      event_data:
        RideRequestFailed:
          - field: "reason"
            value: "Driver did not accept"
```

**Visualize Saga** :
```bash
$ pubsub-tools saga visualize BookingFlowSaga --output booking_flow.png
```

```
Generated flow diagram:

RideRequested
     ↓
DriverMatched ───(timeout 30s)──→ DriverReleased ⚠️
     ↓                                  ↓
DriverAccepted                    MatchCancelled
     ↓
TripStarted
     ↓
TripCompleted
```

---

## 🎮 Gaming Platform - Leaderboard System

### Contexte
Plateforme gaming avec leaderboards temps réel et achievements.

### Problématiques
- **Event storm** : Millions de score updates/minute
- **Eventually consistent** : Leaderboards approximatifs OK
- **CQRS** : Write optimized / Read optimized

### Solution avec PubSub DevTools

#### 1. CQRS Pattern

```python
# Command side (optimized for writes)
@command_handler
async def submit_score(cmd: SubmitScoreCommand):
    """Submit player score"""

    # Validate
    if not validate_score(cmd.score):
        raise InvalidScoreError()

    # Store in fast write store
    await event_store.append(
        stream_id=f"player-{cmd.player_id}",
        event=ScoreSubmitted(
            player_id=cmd.player_id,
            game_id=cmd.game_id,
            score=cmd.score,
            timestamp=utcnow()
        )
    )

# Query side (optimized for reads)
@query_handler
async def get_leaderboard(query: GetLeaderboardQuery):
    """Get leaderboard (eventually consistent)"""

    # Read from denormalized read model
    return await leaderboard_cache.get_top_players(
        game_id=query.game_id,
        limit=query.limit
    )

# Projection builder (async update read model)
@event_handler("ScoreSubmitted")
async def update_leaderboard_projection(event: ScoreSubmitted):
    """Update read model asynchronously"""

    await leaderboard_cache.update_score(
        player_id=event.player_id,
        game_id=event.game_id,
        score=event.score
    )
```

#### 2. Event Deduplication

```python
# Prevent double-scoring
@deduplication(
    key_func=lambda e: f"{e.player_id}:{e.game_id}:{e.round_id}",
    window_seconds=60
)
@event_handler("ScoreSubmitted")
async def process_score(event: ScoreSubmitted):
    """Process score (idempotent)"""
    # Will only process once even if received multiple times
    await update_player_stats(event)
```

---

## 📊 Résumé : Value Proposition par Secteur

| Secteur | Pain Points | Solution PubSub DevTools | Business Value |
|---------|-------------|-------------------------|----------------|
| **E-Commerce** | Orders perdus, debugging difficile | Event tracing, flow analysis | ↓ Support tickets, ↑ Customer satisfaction |
| **Banking** | Compliance, performance critique | Audit trail, SLO monitoring | Régulation OK, 0 downtime |
| **Social Media** | Rate limiting, volume élevé | Batch processing, rate limiting | ↓ Infrastructure costs 40% |
| **Ride-Sharing** | Saga complexity, geo-distributed | Saga orchestration, testing | ↓ Failed bookings 80% |
| **Gaming** | Event storms, consistency | CQRS, deduplication | ↑ Throughput 10x |

---

## 🎯 Common Patterns Across Use Cases

### 1. **Observability First**
Tous les cas nécessitent : metrics, tracing, logging structuré.

### 2. **Reliability Patterns**
Circuit breakers, retries, DLQ sont universels.

### 3. **Testing Strategy**
Scenario testing + chaos engineering = confidence en production.

### 4. **Performance Optimization**
Batching, connection pooling, async = handle volume.

### 5. **Compliance & Audit**
Audit trail automatique = regulators happy.

---

**Next Steps** : Choisir votre use case et démarrer avec un quick win ! 🚀
