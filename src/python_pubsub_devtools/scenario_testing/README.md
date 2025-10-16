# Scenario Testing Framework

Declarative scenario testing with chaos engineering for event-driven architectures.

## Key Features

- **Zero Coupling by Default**: No hardcoded dependencies on application event classes
- **Flexible Event Registry**: Optional registration of application event classes
- **Declarative YAML Scenarios**: Define test scenarios in YAML
- **Chaos Engineering**: Inject failures, delays, drops, and network latency
- **Event Recording**: Record and replay event flows
- **Assertions**: Validate behavior with event count and value assertions

## Chaos Engineering - Event Injection

### Zero Coupling (Default)

By default, the ChaosInjector creates event instances using SimpleNamespace without any dependency on your application's event classes.

### With Event Registry (Optional Coupling)

If you want to use your application's actual event classes, provide an event registry.

See examples/chaos_injector_usage.py for detailed examples.
