# 🎰 Mock Exchange - Moteur de Rejeu de Données de Marché

Un exchange simulé qui permet de rejouer des fichiers de données de marché historiques (chandeliers) pour le backtesting, le débogage et les tests d'intégration.

## 🎯 Concept

Le Mock Exchange fonctionne comme un moteur de rejeu de données. Vous lui fournissez un fichier de données de chandeliers (par exemple, un `.csv` ou `.json`), et il
publiera les événements de marché correspondants sur le bus de services, en respectant le timing original des données.

Cela permet de tester vos agents de trading et de risque contre des données de marché réelles de manière reproductible et contrôlée.

## 🌐 Web Dashboard (Port 5557) ⭐

Un tableau de bord web interactif est fourni pour gérer et lancer les rejeux de données.

```bash
# Lancer le dashboard via le CLI unifié
pubsub-tools mock-exchange --config devtools_config.yaml

# Ouvrir dans le navigateur
open http://localhost:5557
```

### Fonctionnalités du Dashboard

- **📁 Gestion des Fichiers** : Uploadez, listez et supprimez vos fichiers de données de marché (CSV, JSON).
- **▶️ Lancement de Rejeu** : Démarrez une simulation à partir d'un fichier sélectionné en un seul clic.
- **📊 Vue d'Ensemble** : Visualisez les fichiers disponibles avec leur taille et date de création.
- **🔗 Intégration** : Liens de navigation vers les autres outils DevTools.

---

## 🚀 Usage Rapide

### Étape 1 : Préparer un Fichier de Données

Créez un fichier CSV ou JSON contenant vos données de chandeliers. Le fichier doit être trié par date et contenir au minimum une colonne `timestamp`. Les autres
colonnes (`open`, `high`, `low`, `close`, `volume`) seront incluses dans l'événement.

**Exemple `market_data.csv`:**

```csv
timestamp,open,high,low,close,volume
1672531200,20000.5,20010.0,19990.2,20005.1,10.5
1672531260,20005.1,20025.0,20002.3,20020.4,12.2
1672531320,20020.4,20030.1,20015.5,20018.9,8.7
...
```

### Étape 2 : Lancer le Serveur

Démarrez le serveur Mock Exchange en utilisant le CLI.

```bash
pubsub-tools mock-exchange --config /path/to/your/devtools_config.yaml
```

### Étape 3 : Utiliser l'Interface Web

1. Ouvrez `http://localhost:5557` dans votre navigateur.
2. Utilisez le formulaire "Upload New Replay File" pour téléverser votre fichier `market_data.csv`.
3. Une fois uploadé, le fichier apparaîtra dans la liste "Available Replay Files".
4. Cliquez sur le bouton **"Start Replay"** à côté de votre fichier.

### Résultat

Le Mock Exchange commencera à lire le fichier et à publier des événements `MarketPriceUpdated` sur le bus de services de votre application pour chaque ligne du fichier,
simulant ainsi un flux de marché en direct.

## 🔧 API REST

Le serveur expose une API REST simple pour une intégration programmatique.

### Endpoints Principaux

- `GET /api/replay/files`
    - **Description** : Liste tous les fichiers de rejeu disponibles.
    - **Réponse** : `[{ "filename": "...", "size_kb": ..., "created_at": ... }]`

- `POST /api/replay/upload`
    - **Description** : Uploade un nouveau fichier de rejeu.
    - **Body** : `multipart/form-data` avec un champ `file`.

- `DELETE /api/replay/files/<filename>`
    - **Description** : Supprime un fichier de rejeu.

- `POST /api/replay/start`
    - **Description** : Démarre le rejeu d'un fichier.
    - **Body** : `{"filename": "market_data.csv"}`

### Exemple avec `curl`

```bash
# Lister les fichiers
curl http://localhost:5557/api/replay/files

# Uploader un fichier
curl -X POST -F "file=@/path/to/market_data.csv" http://localhost:5557/api/replay/upload

# Démarrer un rejeu
curl -X POST -H "Content-Type: application/json" -d '{"filename": "market_data.csv"}' http://localhost:5557/api/replay/start
```

## 💡 Bonnes Pratiques

- **Nommage** : Utilisez des noms de fichiers descriptifs (ex: `BTCUSDT_1m_2023-01.csv`).
- **Nettoyage** : Supprimez les fichiers de rejeu inutilisés via l'interface web ou l'API.
- **Format de Données** : Assurez-vous que vos données sont propres et triées chronologiquement pour une simulation correcte.

## ⚠️ Limitations

- Le rejeu se fait en "temps machine" (aussi vite que possible) et ne respecte pas les deltas de temps réels entre les chandeliers. La logique de temporisation est gérée
  par les consommateurs des événements.
- La validation du contenu des fichiers (CSV/JSON) est basique. Des fichiers mal formatés peuvent causer des erreurs lors du rejeu.

