# 📚 Documentation PubSub DevTools

Documentation complète du framework PubSub DevTools pour architectures événementielles.

---

## 📂 Structure de la Documentation

La documentation est organisée en 5 catégories principales :

### 🏗️ [Architecture](./architecture/)
Documentation de l'architecture système et cas d'usage.
- [01_ARCHITECTURE.md](./architecture/01_ARCHITECTURE.md) - Principes, structure modulaire, composants
- [02_USE_CASES.md](./architecture/02_USE_CASES.md) - Cas d'usage concrets (e-commerce, banking, etc.)

### 📋 [Planning](./planning/)
Vision produit, roadmap et priorités.
- [03_METRICS.md](./planning/03_METRICS.md) - Event Metrics Collector (feature principale)
- [04_ROADMAP.md](./planning/04_ROADMAP.md) - Roadmap 2025-2026 (8 phases)
- [05_QUICK_WINS.md](./planning/05_QUICK_WINS.md) - Améliorations rapides à fort impact

### 📘 [Guides](./guides/)
Guides pratiques d'utilisation et migration.
- [CLI_USAGE.md](guides/10_CLI_USAGE.md) - Guide complet du CLI
- [06_MIGRATION_GUIDE.md](./guides/06_MIGRATION_GUIDE.md) - Migration depuis versions précédentes

### 🔧 [Implementation](./implementation/)
Résumés techniques d'implémentation.
- [07_IMPLEMENTATION_SUMMARY.md](./implementation/07_IMPLEMENTATION_SUMMARY.md) - Metrics Collector
- [08_MIGRATION_SUMMARY.md](./implementation/08_MIGRATION_SUMMARY.md) - Scenario Engine Migration
- [09_PACKAGE_SETUP_SUMMARY.md](./implementation/09_PACKAGE_SETUP_SUMMARY.md) - Configuration package

### ✅ [Status](./status/)
Historique et statut du projet (référence).
- [99_SETUP_COMPLETE.md](./status/99_SETUP_COMPLETE.md) - Setup initial
- [99_RENAMING_COMPLETE.md](./status/99_RENAMING_COMPLETE.md) - Renommages
- [99_INSTALLATION_SUCCESS.md](./status/99_INSTALLATION_SUCCESS.md) - Vérification installation

---

## 🚀 Par où commencer ?

### Si vous découvrez le projet :
1. [**Architecture**](./architecture/01_ARCHITECTURE.md) - Comprendre la vision globale
2. [**Use Cases**](./architecture/02_USE_CASES.md) - Voir des exemples concrets
3. [**Metrics**](./planning/03_METRICS.md) - Commencer à utiliser les métriques

### Si vous voulez utiliser le CLI :
👉 [**CLI Usage Guide**](guides/10_CLI_USAGE.md) - Guide complet avec exemples

### Si vous voulez contribuer :
1. [**Quick Wins**](./planning/05_QUICK_WINS.md) - Améliorations prioritaires
2. [**Roadmap**](./planning/04_ROADMAP.md) - Vision long terme
3. [**Architecture**](./architecture/01_ARCHITECTURE.md) - Structure technique

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

| Feature | Port | Command |
|---------|------|---------|
| Event Flow | 5555 | `pubsub-devtools event-flow` |
| Event Recorder | 5556 | `pubsub-devtools event-recorder` |
| Mock Exchange | 5557 | `pubsub-devtools mock-exchange` |
| Test Scenarios | 5558 | `pubsub-devtools test-scenarios` |
| **Dashboard** | All | `pubsub-devtools dashboard` |

---

**Version**: 0.2.0 | **Last Updated**: 2025-10-14 | **License**: MIT
