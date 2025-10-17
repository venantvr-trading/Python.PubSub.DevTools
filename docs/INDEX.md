# 📚 Python PubSub DevTools - Documentation

Comprehensive development and debugging tools for PubSub-based event-driven architectures.

## 📖 Table of Contents

### 🏗️ Architecture & Concepts

Understanding the system design and use cases.

- [**Architecture Technique**](architecture/01_ARCHITECTURE.md) - System architecture and components

### 📋 Planning & Roadmap

Strategic planning and feature development.

- [**Roadmap**](planning/04_ROADMAP.md) - Product vision and future features
- [**Quick Wins**](planning/05_QUICK_WINS.md) - Immediate improvements and priorities

### 📘 User Guides

Getting started and using the tools.

- [**CLI Usage Guide**](guides/10_CLI_USAGE.md) - Command-line interface reference
- [**Migration Guide**](guides/06_MIGRATION_GUIDE.md) - Migrating from legacy systems

### 🔧 Implementation Details

Technical implementation summaries and migration reports.

- [**Event Metrics Implementation**](implementation/07_IMPLEMENTATION_SUMMARY.md) - Metrics collector implementation
- [**Scenario Engine Migration**](implementation/08_MIGRATION_SUMMARY.md) - Generic scenario testing framework migration

---

## 🚀 Quick Start

```bash
# Install the package
pip install python_pubsub_devtools

# Launch the dashboard (all servers)
pubsub-devtools dashboard

# Launch individual servers
pubsub-devtools event-flow      # Port 5555
pubsub-devtools event-recorder  # Port 5556
pubsub-devtools mock-exchange   # Port 5557
pubsub-devtools test-scenarios  # Port 5558
```

## 📦 Main Features

- **Event Flow Visualization** - Interactive graph of events and agents
- **Event Recorder** - Record and replay event sequences
- **Mock Exchange** - Simulate market data with scenarios
- **Scenario Testing** - Generic scenario testing framework with chaos engineering
- **Event Metrics** - Comprehensive event monitoring and statistics

## 🔗 Links

- [GitHub Repository](https://github.com/venantvr-trading/Python.PubSub.DevTools)
- [Documentation Wiki](https://github.com/venantvr-trading/Python.PubSub.DevTools/wiki)
- [Issues](https://github.com/venantvr-trading/Python.PubSub.DevTools/issues)

---

**Version:** 0.2.0 | **License:** MIT
