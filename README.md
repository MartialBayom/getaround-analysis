# Getaround Analyse des Retards & Optimisation des Prix

> *Aider Getaround à définir la politique de délai minimum entre deux locations et suggérer des prix optimaux aux propriétaires grâce au Machine Learning*

[![Streamlit App](https://img.shields.io/badge/App-Streamlit-FF4B4B?logo=streamlit)](https://getaround-analysis-martialbayom.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python)](https://www.python.org/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikit-learn)](https://scikit-learn.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![MLflow](https://img.shields.io/badge/MLflow-Tracking-0194E2)](https://mlflow.org/)

---

## Objectif

**Comment réduire les conflits liés aux retards sans pénaliser les revenus des propriétaires ?**

Ce projet analyse **21 310 locations** Getaround pour recommander :
1. Un **seuil de délai minimum** entre deux locations consécutives
2. Une **portée** (toutes les voitures ou uniquement les voitures Connect)
3. Un **modèle de pricing ML** pour suggérer des prix optimaux aux propriétaires

🔗 **Dashboard en ligne :** [getaround-analysis-martialbayom.streamlit.app](https://getaround-analysis-martialbayom.streamlit.app/)  
🔗 **API en ligne :** [getaround-api-efhe.onrender.com/docs](https://getaround-api-efhe.onrender.com/docs)

---

## Fonctionnalités

### Analyse des Retards (Dashboard)

- Visualisation de la distribution des retards par type de check-in (Mobile vs Connect)
- Simulation interactive du seuil (30 à 720 min) et de la portée
- Courbe coût/bénéfice : locations bloquées vs cas problématiques résolus
- Recommandation data-driven pour le chef de produit

### Optimisation des Prix (API ML)

- Endpoint `/predict` : suggère un prix journalier basé sur les caractéristiques du véhicule
- Endpoint `/docs` : documentation interactive de l'API
- 3 modèles comparés : Ridge, Random Forest, Gradient Boosting

---

## Résultats

### Analyse des Retards

| Indicateur | Valeur |
|---|---|
| Locations totales | 21 310 |
| En retard au checkout | ~57% des locations terminées |
| Médiane du retard (Mobile) | **+14 min** |
| Médiane du retard (Connect) | **-9 min** |
| Locations impactées par un retard précédent | 270 (14.7%) |

**Recommandation :** Seuil de **60 minutes** sur les voitures **Connect uniquement** en phase pilote.

### Modèle de Pricing

| Modèle | MAE (€) | RMSE (€) | R² |
|---|---|---|---|
| Ridge Regression | ~18€ | ~24€ | ~0.47 |
| **Random Forest ** | **~12€** | **~17€** | **~0.74** |
| Gradient Boosting | ~13€ | ~18€ | ~0.72 |

---

## Structure du projet

```
getaround/
├── app/
│   └── streamlit_app.py              # Dashboard Streamlit
├── data/
│   ├── get_around_delay_analysis.xlsx   # 21 310 locations (analyse retards)
│   └── get_around_pricing_project.csv   # 4 843 véhicules (optimisation prix)
├── models/                           # Modèles entraînés (.pkl)
├── notebooks/
│   ├── 01_eda_delays.ipynb           # Analyse exploratoire des retards
│   └── 02_ml_pricing.ipynb           # ML — optimisation des prix
├── .env.example                      # Variables d'environnement (template)
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Features utilisées pour le pricing

| Feature | Description |
|---|---|
| `mileage` | Kilométrage du véhicule |
| `engine_power` | Puissance moteur (ch) |
| `model_key` | Marque du véhicule |
| `fuel` | Type de carburant (diesel, essence, hybride, électrique) |
| `paint_color` | Couleur de la carrosserie |
| `car_type` | Segment (berline, SUV, cabriolet...) |
| `has_gps` | GPS intégré |
| `has_air_conditioning` | Climatisation |
| `automatic_car` | Boîte automatique |
| `has_getaround_connect` | Technologie Connect (ouverture smartphone) |
| `has_speed_regulator` | Régulateur de vitesse |
| `winter_tires` | Pneus hiver |

---

## Analyse exploratoire — Insights clés

- **57%** des conducteurs rendent la voiture en retard (mobile) vs **37%** (connect)
- Les voitures **Connect** ont une médiane de retard de **-9 min** → rendues en avance en moyenne
- Seulement **1 841 locations** ont une location précédente identifiée → **270 cas impactés** (14.7%)
- Un seuil de **60 min sur Connect** résout **~65% des cas** pour seulement **~1% de revenus affectés**
- La **puissance moteur** est la feature la plus prédictive du prix (corrélation positive forte)

---

## Installation locale

```bash
# Cloner le repo
git clone https://github.com/MartialBayom/getaround-analysis.git
cd getaround-analysis

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Remplir .env avec vos clés si nécessaire

# Lancer le dashboard
streamlit run app/streamlit_app.py
```

---

## API Endpoint `/predict`

```bash
curl -X POST 'https://getaround-api-efhe.onrender.com/predict' \
     -H 'Content-Type: application/json' \
     -d '{"input": [[50000, 120, "Renault", "diesel", "black", "sedan", true, true, true, false, true, false, false]]}'
```

```python
import requests

response = requests.post("https://getaround-api-efhe.onrender.com/predict", json={
    "input": [[50000, 120, "Renault", "diesel", "black", "sedan",
               True, True, True, False, True, False, False]]
})
print(response.json())
# {"prediction": [118]}
```

---

## Infrastructure

```
Jedha (données brutes)
        ↓
Analyse exploratoire (pandas, seaborn, matplotlib)
        ↓
Machine Learning (3 modèles comparés via GridSearchCV + MLflow)
        ↓
API FastAPI (endpoint /predict + /docs)
        ↓
Dashboard Streamlit (déploiement sur Hugging Face)
```

---

## What's next ?

- [ ] **Dashboard interactif complet** — simulation temps réel du seuil par le chef de produit
- [ ] **XGBoost / LightGBM** — tester des modèles plus performants pour le pricing
- [ ] **Feature engineering** — ajouter l'année du véhicule, le nombre de locations précédentes
- [ ] **Monitoring** — détecter le data drift sur les prédictions de prix en production

---

## Auteur

| | Nom | Rôle |
|---|---|---|
|  | **Martial BAYOM** | Data Science |

---

## Sources

| Dataset | Source |
|---|---|
| Get Around Delay Analysis | Jedha AI School |
| Get Around Pricing Project | Jedha AI School |
