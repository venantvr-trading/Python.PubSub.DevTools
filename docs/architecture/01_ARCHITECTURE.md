# 🏗️ Architecture Technique - PubSub DevTools

Architecture d'un framework professionnel pour architectures événementielles.

---

## 🎯 Principes d'Architecture

### 1. **Plugin-Based Architecture**

Extensibilité maximale via plugins et hooks.

### 2. **Backend-Agnostic**

Support de multiples backends (in-memory, Kafka, RabbitMQ, etc.).

### 3. **Zero-Configuration Default**

Fonctionne out-of-the-box avec configuration progressive.

### 4. **Performance First**

Overhead minimal, optimisé pour production.

### 5. **Observability Built-in**

Metrics, logging, tracing intégrés par défaut.

---

## 📦 Structure Modulaire

```
python_pubsub_devtools/
├── core/                    # Core event bus & infrastructure
│   ├── event_bus.py        # Main EventBus class
│   ├── event.py            # Base Event classes
│   ├── handler.py          # Handler registry & execution
│   ├── middleware.py       # Middleware pipeline
│   └── backend/            # Backend implementations
│       ├── memory.py       # In-memory (dev/test)
│       ├── kafka.py        # Kafka adapter
│       ├── rabbitmq.py     # RabbitMQ adapter
│       └── redis.py        # Redis Streams adapter
│
├── observability/           # Monitoring & observability
│   ├── metrics.py          # Metrics collection (Prometheus)
│   ├── tracing.py          # Distributed tracing (OpenTelemetry)
│   ├── logging.py          # Structured logging
│   └── profiler.py         # Performance profiling
│
├── reliability/             # Reliability patterns
│   ├── retry.py            # Retry logic with backoff
│   ├── circuit_breaker.py  # Circuit breaker pattern
│   ├── dlq.py              # Dead Letter Queue
│   ├── deduplication.py    # Event deduplication
│   └── rate_limiter.py     # Rate limiting
│
├── schema/                  # Schema management
│   ├── registry.py         # Schema registry
│   ├── validator.py        # Schema validation
│   ├── versioning.py       # Schema versioning
│   └── migration.py        # Schema migration
│
├── patterns/                # Event-driven patterns
│   ├── saga.py             # Saga orchestration
│   ├── cqrs.py             # CQRS helpers
│   ├── event_sourcing.py   # Event sourcing
│   └── outbox.py           # Transactional outbox
│
├── testing/                 # Testing utilities
│   ├── mock_exchange/      # Market simulation (existing)
│   ├── event_recorder/     # Event recording (existing)
│   ├── scenario_testing/   # Scenario framework (existing)
│   ├── chaos_engineering/  # Chaos injection (existing)
│   ├── fixtures.py         # Test fixtures
│   └── assertions.py       # Custom assertions
│
├── integrations/            # Cloud & third-party integrations
│   ├── aws/
│   │   ├── eventbridge.py
│   │   ├── sqs.py
│   │   └── sns.py
│   ├── azure/
│   │   ├── event_grid.py
│   │   └── event_hubs.py
│   ├── gcp/
│   │   └── pubsub.py
│   └── datadog/
│       └── apm.py
│
├── cli/                     # Command-line interface
│   ├── main.py             # CLI entry point (existing)
│   ├── commands/
│   │   ├── events.py       # Event management commands
│   │   ├── metrics.py      # Metrics commands
│   │   ├── health.py       # Health check commands
│   │   ├── replay.py       # Replay commands
│   │   └── generate.py     # Code generation
│   └── formatters/         # Output formatters
│
├── web/                     # Web dashboard
│   ├── server.py           # FastAPI server
│   ├── api/                # REST API
│   ├── websockets.py       # WebSocket support
│   └── static/             # Frontend assets
│
├── trading/                 # Domain examples (existing)
│   ├── indicators.py
│   └── candle_patterns.py
│
└── plugins/                 # Plugin system
    ├── base.py             # Plugin base class
    └── loader.py           # Plugin loader
```

---

## 🔄 Core Architecture

### Event Bus - Hub Central

```python
class EventBus:
    """Central event bus with plugin architecture"""

    def __init__(
            self,
            backend: Backend = InMemoryBackend(),
            middleware: List[Middleware] = None,
            config: Config = None,
    ):
        self.backend = backend
        self.handlers = HandlerRegistry()
        self.middleware_pipeline = MiddlewarePipeline(middleware or [])
        self.plugins = PluginManager()
        self.config = config or Config.from_env()

        # Built-in observability
        self.metrics = MetricsCollector()
        self.tracer = Tracer()
        self.logger = StructuredLogger()

    async def publish(self, event: Event) -> None:
        """Publish event through middleware pipeline"""
        with self.tracer.span("event.publish"):
            # Pre-processing middleware
            event = await self.middleware_pipeline.process_outbound(event)

            # Publish to backend
            await self.backend.publish(event)

            # Post-processing
            await self.plugins.on_event_published(event)
            self.metrics.record_event(event)

    async def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe handler to event type"""
        wrapped_handler = self._wrap_handler(handler)
        self.handlers.register(event_type, wrapped_handler)

    def _wrap_handler(self, handler: Callable) -> Callable:
        """Wrap handler with observability & error handling"""

        @wraps(handler)
        async def wrapped(event: Event):
            with self.tracer.span(f"handler.{handler.__name__}"):
                start_time = time.time()

                try:
                    result = await handler(event)
                    duration_ms = (time.time() - start_time) * 1000

                    self.metrics.record_handler_success(
                        handler.__name__,
                        duration_ms
                    )
                    return result

                except Exception as e:
                    self.logger.exception(f"Handler failed: {handler.__name__}")
                    self.metrics.record_handler_error(handler.__name__)

                    # DLQ handling
                    await self.dlq.send(event, error=e)
                    raise

        return wrapped
```

---

### Middleware Pipeline

```python
class MiddlewarePipeline:
    """Pipeline de middleware pour transformation des events"""

    def __init__(self, middlewares: List[Middleware]):
        self.middlewares = middlewares

    async def process_outbound(self, event: Event) -> Event:
        """Process event before publishing"""
        for middleware in self.middlewares:
            event = await middleware.process_outbound(event)
        return event

    async def process_inbound(self, event: Event) -> Event:
        """Process event before handling"""
        for middleware in reversed(self.middlewares):
            event = await middleware.process_inbound(event)
        return event


# Example middlewares
class CorrelationMiddleware(Middleware):
    """Inject correlation ID"""
    async def process_outbound(self, event: Event) -> Event:
        if not event.correlation_id:
            event.correlation_id = str(uuid.uuid4())
        return event


class ValidationMiddleware(Middleware):
    """Validate event schema"""
    async def process_outbound(self, event: Event) -> Event:
        validator.validate(event)
        return event


class EncryptionMiddleware(Middleware):
    """Encrypt sensitive fields"""
    async def process_outbound(self, event: Event) -> Event:
        for field in event.sensitive_fields():
            event[field] = encrypt(event[field])
        return event
```

---

### Backend Abstraction

```python
class Backend(ABC):
    """Abstract backend interface"""

    @abstractmethod
    async def publish(self, event: Event) -> None:
        """Publish event to backend"""
        pass

    @abstractmethod
    async def subscribe(
        self,
        event_type: str,
        handler: Callable
    ) -> None:
        """Subscribe to event type"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connections"""
        pass


class KafkaBackend(Backend):
    """Kafka implementation"""

    def __init__(
        self,
        bootstrap_servers: List[str],
        group_id: str,
        **config
    ):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            **config
        )
        self.consumer = AIOKafkaConsumer(
            group_id=group_id,
            bootstrap_servers=bootstrap_servers,
            **config
        )

    async def publish(self, event: Event) -> None:
        topic = event.__class__.__name__
        value = event.json().encode()

        await self.producer.send(
            topic=topic,
            value=value,
            key=event.correlation_id.encode()
        )


class RedisStreamsBackend(Backend):
    """Redis Streams implementation"""
    # ... similar interface
```

---

## 🔌 Plugin System

```python
class Plugin(ABC):
    """Base plugin interface"""

    def on_event_published(self, event: Event) -> None:
        """Called after event published"""
        pass

    def on_handler_executed(
        self,
        handler: str,
        event: Event,
        duration_ms: float
    ) -> None:
        """Called after handler execution"""
        pass

    def on_error(self, error: Exception, event: Event) -> None:
        """Called on error"""
        pass


# Example: Datadog APM Plugin
class DatadogPlugin(Plugin):
    def __init__(self, api_key: str):
        self.client = DatadogClient(api_key)

    def on_handler_executed(self, handler, event, duration_ms):
        self.client.send_metric(
            name=f"handler.{handler}.duration",
            value=duration_ms,
            tags=[f"event_type:{event.__class__.__name__}"]
        )


# Register plugin
event_bus.register_plugin(DatadogPlugin(api_key="..."))
```

---

## 📊 Observability Stack

### 1. Metrics (Prometheus)

```python
class MetricsCollector:
    """Prometheus metrics"""

    def __init__(self):
        # Counters
        self.events_published = Counter(
            'events_published_total',
            'Total events published',
            ['event_type']
        )

        # Histograms
        self.handler_duration = Histogram(
            'handler_duration_seconds',
            'Handler execution duration',
            ['handler', 'event_type']
        )

        # Gauges
        self.active_handlers = Gauge(
            'active_handlers',
            'Number of active handlers'
        )

    def record_event(self, event: Event):
        self.events_published.labels(
            event_type=event.__class__.__name__
        ).inc()
```

### 2. Tracing (OpenTelemetry)

```python
class Tracer:
    """OpenTelemetry tracing"""

    def __init__(self, service_name: str):
        self.tracer = trace.get_tracer(service_name)

    @contextmanager
    def span(self, name: str):
        with self.tracer.start_as_current_span(name) as span:
            span.set_attribute("service.name", "pubsub-devtools")
            yield span
```

### 3. Logging (Structured)

```python
class StructuredLogger:
    """JSON structured logging"""

    def log_event(self, event: Event, **extra):
        logger.info(
            "event_published",
            extra={
                "event_type": event.__class__.__name__,
                "event_id": event.id,
                "correlation_id": event.correlation_id,
                "timestamp": event.timestamp.isoformat(),
                **extra
            }
        )
```

---

## 🛡️ Reliability Patterns

### Circuit Breaker

```python
class CircuitBreaker:
    """Circuit breaker pattern"""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        recovery_timeout: int = 300
    ):
        self.failure_threshold = failure_threshold
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None

    async def call(self, func: Callable, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError()

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise


@circuit_breaker(failure_threshold=5, timeout=60)
@event_handler("ExternalAPICall")
async def call_api(event):
    response = await http_client.post(url, data=event.data)
    return response
```

---

## 🧪 Testing Architecture

### Test Fixtures

```python
# tests/fixtures.py
@pytest.fixture
def event_bus():
    """Isolated event bus for testing"""
    bus = EventBus(backend=InMemoryBackend())
    yield bus
    bus.close()


@pytest.fixture
def event_recorder(event_bus):
    """Record events for assertions"""
    recorder = EventRecorder()
    recorder.start_recording(event_bus)
    yield recorder
    recorder.stop_recording()


@pytest.fixture
def mock_exchange():
    """Mock exchange for trading tests"""
    return ScenarioBasedMockExchange(
        scenario=MarketScenario.BULL_RUN,
        initial_price=50000.0
    )
```

### Assertion Helpers

```python
# tests/assertions.py
def assert_event_published(recorder, event_type, count=1):
    """Assert event was published"""
    events = recorder.get_events(event_type)
    assert len(events) == count, f"Expected {count} {event_type}, got {len(events)}"


def assert_event_order(recorder, *event_types):
    """Assert events published in order"""
    actual_order = [e.type for e in recorder.get_all()]
    expected_order = list(event_types)
    assert actual_order == expected_order
```

---

## 🚀 Deployment Architecture

### Docker Compose Setup

```yaml
version: '3.8'

services:
  pubsub-devtools:
    image: pubsub-devtools:latest
    environment:
      - EVENT_BUS_BACKEND=kafka
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - METRICS_ENABLED=true
      - TRACING_ENABLED=true
    ports:
      - "8080:8080"  # API
      - "9090:9090"  # Metrics
    depends_on:
      - kafka
      - prometheus

  kafka:
    image: confluentinc/cp-kafka:latest
    # ... kafka config

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
```

---

## 📈 Performance Considerations

### 1. Async by Default

```python
# Tout async pour performance maximale
async def publish(self, event: Event):
    await self.backend.publish(event)
```

### 2. Connection Pooling

```python
# Pool de connexions
self.pool = ConnectionPool(
    max_connections=100,
    max_idle_time=300
)
```

### 3. Event Batching

```python
# Batch pour réduire overhead
async def publish_batch(self, events: List[Event]):
    await self.backend.publish_batch(events)
```

### 4. Zero-Copy Serialization

```python
# msgpack ou protobuf pour performance
serializer = MsgPackSerializer()  # Plus rapide que JSON
```

---

## 🔒 Security Considerations

### 1. Event Encryption

```python
# Encryption at rest
encryptor = FieldEncryptor(key=os.getenv("ENCRYPTION_KEY"))
event.sensitive_data = encryptor.encrypt(event.sensitive_data)
```

### 2. Authentication

```python
# API authentication
@require_auth(roles=["admin"])
async def get_events(request):
    return await event_store.get_all()
```

### 3. Audit Logging

```python
# Audit trail
audit_logger.log_access(
    user=request.user,
    action="read_events",
    resource="event_store"
)
```

---

## 📚 Resources

- [Event-Driven Architecture Patterns](https://martinfowler.com/articles/201701-event-driven.html)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)
- [Saga Pattern](https://microservices.io/patterns/data/saga.html)
- [Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)

---

**Version**: 1.0.0
**Last Updated**: 2025-10-13
