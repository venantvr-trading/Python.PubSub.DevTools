# 📚 Documentation PubSub DevTools

Documentation complète du framework PubSub DevTools pour architectures événementielles.

---

## 📂 Structure de la Documentation

La documentation est organisée en 4 catégories principales :

### 🏗️ [Architecture](./architecture/01_ARCHITECTURE.md)

Documentation de l'architecture système.

- [01_ARCHITECTURE.md](./architecture/01_ARCHITECTURE.md) - Principes, structure modulaire, composants

### 📋 [Planning](./planning/04_ROADMAP.md)

Vision produit, roadmap et priorités.

- [04_ROADMAP.md](./planning/04_ROADMAP.md) - Roadmap 2025-2026 (8 phases)
- [05_QUICK_WINS.md](./planning/05_QUICK_WINS.md) - Améliorations rapides à fort impact

### 📘 [Guides](./guides/06_MIGRATION_GUIDE.md)

Guides pratiques d'utilisation et migration.

- [10_CLI_USAGE.md](./guides/10_CLI_USAGE.md) - Guide complet du CLI
- [06_MIGRATION_GUIDE.md](./guides/06_MIGRATION_GUIDE.md) - Migration depuis versions précédentes

### 🔧 [Implementation](./implementation/07_IMPLEMENTATION_SUMMARY.md)

Résumés techniques d'implémentation.

- [07_IMPLEMENTATION_SUMMARY.md](./implementation/07_IMPLEMENTATION_SUMMARY.md) - Metrics Collector
- [08_MIGRATION_SUMMARY.md](./implementation/08_MIGRATION_SUMMARY.md) - Scenario Engine Migration

---

## 🚀 Par où commencer ?

### Si vous découvrez le projet :

1. [**Architecture**](./architecture/01_ARCHITECTURE.md) - Comprendre la vision globale
2. [**Roadmap**](./planning/04_ROADMAP.md) - Voir la vision long terme

### Si vous voulez utiliser le CLI :

👉 [**CLI Usage Guide**](./guides/10_CLI_USAGE.md) - Guide complet avec exemples

### Si vous voulez contribuer :

1. [**Quick Wins**](./planning/05_QUICK_WINS.md) - Améliorations prioritaires
2. [**Architecture**](./architecture/01_ARCHITECTURE.md) - Structure technique

### Si vous migrez depuis une ancienne version :

👉 [**Migration Guide**](./guides/06_MIGRATION_GUIDE.md)

---

## 📊 État actuel du projet

### ✅ Implémenté

- Event Metrics Collector ⭐
- Event Flow Visualization (React Flow)
- Event Recorder & Replay
- Mock Exchange with scenarios
- Scenario Testing Framework with Chaos Engineering
- CLI tools (`pubsub-devtools`)

### 🚧 En cours

Voir [Quick Wins](./planning/05_QUICK_WINS.md) pour les prochaines étapes.

---

## 🔗 Quick Links

| Feature        | Port | Command                          |
|----------------|------|----------------------------------|
| Event Flow     | 5555 | `pubsub-devtools event-flow`     |
| Event Recorder | 5556 | `pubsub-devtools event-recorder` |
| Mock Exchange  | 5557 | `pubsub-devtools mock-exchange`  |
| Test Scenarios | 5558 | `pubsub-devtools test-scenarios` |
| **Dashboard**  | All  | `pubsub-devtools dashboard`      |

---

**Version**: 0.2.0 | **Last Updated**: 2025-10-14 | **License**: MIT
