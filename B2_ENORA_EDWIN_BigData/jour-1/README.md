# Jour 1 — BigData Commerce Analytics (B2 · Sup de Vinci Rennes)
Binôme : Enora & Edwin · Source : DummyJSON · Collecte du 25/11/2026

## Contenu
- `notebooks/01_atelier_exploration_sources.ipynb` — Atelier 1 (exécuté)
- `notebooks/02_atelier_profilage_pandas.ipynb` — Atelier 2 (exécuté)
- `livrables/SYNTHESE_ATELIER1.md` — synthèse d'une page (atelier 1)
- `livrables/NOTE_QUALITE.md` — note de qualité (atelier 2)
- `livrables/CADRAGE_5V_ATELIER3.md` — page de cadrage des 5V (atelier 3)
- `scripts/01_collecte_dummyjson.py` — collecte des données de l'API
- `consignes/` — fiche étudiant
- `data/` — données brutes et tables dérivées (**non versionné**, ignoré par git)

## Récupérer les données (le dossier `data/` n'est pas poussé)
```bash
# depuis la racine du dépôt
source venv/bin/activate
pip install -r requirements.txt
python B2_ENORA_EDWIN_BigData/jour-1/scripts/01_collecte_dummyjson.py
```
Le script remplit `jour-1/data/raw/` et `jour-1/data/processed/`. Les notebooks se lancent ensuite depuis `jour-1/notebooks/`.

`order_date` est une date synthétique générée pour l'exercice : elle ne vient pas de l'API.
