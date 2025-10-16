# Event Flow API & Scanner

Architecture moderne pour event_flow avec séparation API/Scanner.

## Architecture

```
┌─────────────────────┐       POST /api/graph      ┌──────────────────┐
│   Scanner Service   │ ─────────────────────────> │  Event Flow API  │
│  (analyse le code)  │     (envoie les dots)      │  (serveur Flask) │
└─────────────────────┘                            └──────────────────┘
                                                           │
                                                           │ GET /graph/...
                                                           ▼
                                                    ┌──────────────────┐
                                                    │  Utilisateurs    │
                                                    │  (interface web) │
                                                    └──────────────────┘
```

## Composants

### 1. Event Flow API (Serveur Flask)

Serveur web qui expose:
- **Interface Web** : Visualisation interactive des graphes (port 5555)
- **API REST** : Endpoints pour recevoir/servir les données des graphes

#### Routes API

```
POST   /api/graph              - Recevoir et stocker les données DOT
GET    /api/graph/status       - Statut du cache
GET    /api/graph/<type>       - Récupérer un graphe spécifique
DELETE /api/graph/<type>       - Supprimer un graphe du cache
DELETE /api/graph              - Vider tout le cache
```

#### Démarrer l'API

```bash
# Via CLI
pubsub-tools event-flow --config devtools_config.yaml

# Ou directement
python -m python_pubsub_devtools.event_flow.serve_event_flow
```

### 2. Scanner (Service autonome)

Service qui scanne le code et pousse les graphes vers l'API.

**Modes:**
- **One-shot** : Scanne une fois et sort
- **Continu** : Scanne à intervalle régulier

#### Utiliser le Scanner

**One-shot (via CLI):**
```bash
python -m python_pubsub_devtools.event_flow.scanner \
    --agents-dir ../python_pubsub_risk/agents \
    --events-dir ../python_pubsub_risk/events \
    --api-url http://localhost:5555 \
    --one-shot
```

**Continu (via CLI):**
```bash
python -m python_pubsub_devtools.event_flow.scanner \
    --agents-dir ../python_pubsub_risk/agents \
    --events-dir ../python_pubsub_risk/events \
    --api-url http://localhost:5555 \
    --interval 60
```

**Programmatique:**
```python
from pathlib import Path
from python_pubsub_devtools.event_flow import EventFlowScanner

# One-shot
scanner = EventFlowScanner(
    agents_dir=Path("agents"),
    events_dir=Path("events"),
    api_url="http://localhost:5555"
)
results = scanner.scan_once()

# Continu
scanner = EventFlowScanner(
    agents_dir=Path("agents"),
    events_dir=Path("events"),
    api_url="http://localhost:5555",
    interval=60  # secondes
)
scanner.run_continuous()
```

### 3. Storage (Cache)

Système de cache thread-safe pour stocker les graphes en mémoire.

**Features:**
- Cache en mémoire avec verrous thread-safe
- Persistance optionnelle sur disque (JSON)
- Stockage de DOT + SVG + métadonnées
- Timestamps et statistiques

**Usage:**
```python
from python_pubsub_devtools.event_flow import get_storage, GraphData

# Récupérer l'instance singleton
storage = get_storage()

# Stocker un graphe
graph_data = GraphData(
    graph_type="complete",
    dot_content="digraph {...}",
    stats={"events": 10, "agents": 5}
)
storage.store(graph_data)

# Récupérer un graphe
cached = storage.get("complete")
if cached:
    print(cached.dot_content)

# Statut du cache
status = storage.get_status()
print(status)
```

## API REST - Détails

### POST /api/graph

Recevoir et stocker les données d'un graphe.

**Request:**
```json
{
  "graph_type": "simplified|complete|full-tree",
  "dot_content": "digraph {...}",
  "svg_content": "<svg>...</svg>",  // optionnel
  "namespaces": ["market_data", "position"],  // optionnel
  "stats": {
    "events": 10,
    "agents": 5
  }  // optionnel
}
```

**Response (201):**
```json
{
  "status": "success",
  "graph_type": "complete",
  "timestamp": "2025-10-16T14:30:00"
}
```

### GET /api/graph/status

Obtenir le statut du cache.

**Response (200):**
```json
{
  "total_graphs": 3,
  "persist_enabled": false,
  "graphs": {
    "simplified": {
      "timestamp": "2025-10-16T14:30:00",
      "has_svg": true,
      "stats": {"events": 10, "agents": 5}
    },
    "complete": {...},
    "full-tree": {...}
  }
}
```

### GET /api/graph/<graph_type>

Récupérer un graphe du cache.

**Query Parameters:**
- `format`: `dot` (défaut) | `svg` | `json`

**Response:**
- `format=dot`: Retourne le contenu DOT (text/plain)
- `format=svg`: Retourne le SVG (image/svg+xml)
- `format=json`: Retourne les métadonnées complètes (application/json)

**Exemple:**
```bash
# Récupérer DOT
curl http://localhost:5555/api/graph/complete?format=dot

# Récupérer SVG
curl http://localhost:5555/api/graph/complete?format=svg > complete.svg

# Récupérer métadonnées
curl http://localhost:5555/api/graph/complete?format=json | jq .
```

### DELETE /api/graph/<graph_type>

Supprimer un graphe du cache.

**Response (200):**
```json
{
  "status": "success",
  "message": "Graph \"complete\" cleared from cache"
}
```

### DELETE /api/graph

Vider tout le cache.

**Response (200):**
```json
{
  "status": "success",
  "message": "All graphs cleared from cache"
}
```

## Comportement du Cache

### Route /graph/<graph_type> (Interface Web)

La route existante `/graph/<graph_type>` (utilisée par l'interface web) utilise maintenant le cache:

1. **Si filtres par défaut** (pas de filtrage namespace/failed/rejected):
   - Vérifie le cache
   - Si trouvé: retourne le SVG du cache
   - Sinon: génère à la volée (fallback)

2. **Si filtres appliqués**:
   - Génère toujours à la volée (le cache ne gère pas encore les variantes filtrées)

**Avantages:**
- Réponses rapides pour les vues par défaut
- Les filtres fonctionnent toujours (génération à la volée)
- Compatibilité ascendante complète

## Workflow Typique

### Setup

1. **Démarrer l'API:**
```bash
pubsub-tools event-flow --config devtools_config.yaml
```

2. **Lancer le scanner** (dans un autre terminal):
```bash
python -m python_pubsub_devtools.event_flow.scanner \
    --agents-dir ../python_pubsub_risk/agents \
    --events-dir ../python_pubsub_risk/events \
    --api-url http://localhost:5555 \
    --interval 60
```

3. **Ouvrir l'interface web:**
```
http://localhost:5555
```

### CI/CD Integration

**Dans votre pipeline CI/CD:**
```bash
# Scanner one-shot pour mettre à jour les graphes
python -m python_pubsub_devtools.event_flow.scanner \
    --agents-dir agents \
    --api-url https://event-flow.mycompany.com \
    --one-shot

# Ou en tant que job schedulé (cron/k8s CronJob)
# Scanne toutes les heures
0 * * * * python -m python_pubsub_devtools.event_flow.scanner \
    --agents-dir agents \
    --api-url https://event-flow.mycompany.com \
    --one-shot
```

## Migration depuis l'ancienne version

L'ancienne version (génération à la volée) continue de fonctionner:

**Ancien code:**
```python
# Toujours valide - génère à la volée
http://localhost:5555/graph/complete
```

**Nouvelle architecture:**
```python
# 1. Scanner pousse vers l'API
scanner.scan_once()

# 2. API sert depuis le cache
http://localhost:5555/graph/complete  # Utilise le cache si disponible

# 3. API REST pour intégrations
http://localhost:5555/api/graph/complete?format=dot
```

## Avantages

1. **Découplage** : Scanner et API peuvent tourner séparément
2. **Performance** : Cache réduit la génération coûteuse
3. **Scalabilité** : Plusieurs scanners peuvent pousser vers une API
4. **Flexibilité** : Scanner peut être déclenché par CI/CD
5. **Compatibilité** : L'ancienne interface fonctionne toujours (fallback)

## Notes

- Le cache est en mémoire par défaut (perdu au redémarrage de l'API)
- La persistance sur disque peut être activée via `GraphStorage(persist_path=...)`
- Les filtres namespace/failed/rejected continuent de générer à la volée
- Le scanner nécessite `requests` (installé avec les dépendances du package)
