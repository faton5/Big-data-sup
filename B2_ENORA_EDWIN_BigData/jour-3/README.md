# Jour 3 - Commerce Analytics

Le TP3 reprend les données MongoDB du jour 2, remplace les identifiants clients par des pseudonymes et crée des analyses et un tableau de bord interactif.

## Fichiers à regarder

- `atelier_jour3.ipynb` : préparation, HMAC, vérifications et trois graphiques commentés.
- `app_streamlit.py` : tableau de bord du TP3, alimenté uniquement par les deux fichiers Parquet pseudonymisés.
- `data/` : commandes et paiements pseudonymisés, créés localement par le notebook.
- `figures/` : les trois graphiques exportés en PNG.
- `DOCUMENTATION_TP3.md` et `output/pdf/Documentation_TP3_BigData.pdf` : architecture, sécurité, résultats et trame pour l'oral.

## Ouvrir le tableau de bord du TP3

Depuis le dossier `jour-3` :

```bash
../jour-2/venv/bin/python -m streamlit run app_streamlit.py --server.address 127.0.0.1 --server.port 8501
```

Ouvrir **http://127.0.0.1:8501/** et garder le terminal ouvert. Le menu propose une vue d'ensemble, les catégories, les paiements, les clients, l'exploration des données et une présentation guidée. Pour arrêter le serveur : `Ctrl+C` dans le terminal.

La page des catégories montre d'abord les dix principales pour faciliter la lecture ; la case « Afficher toutes les catégories » permet de voir le classement complet. Le tableau de bord dispose d'un thème clair et d'un thème sombre.

Les deux fichiers Parquet doivent déjà avoir été créés par le notebook. Le dashboard n'a pas besoin de MongoDB ou de la clé pour afficher ces fichiers.

## Relancer le notebook

Depuis `jour-3`, démarrer MongoDB si nécessaire, activer l'environnement du TP2 et charger la clé locale avant Jupyter :

```bash
docker start mongo
source ../jour-2/venv/bin/activate
set -a
. ./.env
set +a
jupyter notebook atelier_jour3.ipynb
```

Dans Jupyter, utiliser le noyau Python de l'environnement du TP2 et exécuter les cellules dans l'ordre. La clé ne doit pas être affichée. Une clé locale est déjà préparée sur cet ordinateur. Elle est nécessaire pour retrouver les mêmes pseudonymes lors d'une nouvelle exécution.

## Installer ou préparer sur un autre ordinateur

Il faut les données des jours 1 et 2 chargées dans MongoDB, puis un environnement Python :

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Pour créer une nouvelle clé privée dans `jour-3`, une seule fois :

```bash
python - <<'PY'
import os
import secrets

fichier = os.open('.env', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fichier, 'w') as sortie:
    sortie.write('PSEUDO_KEY=' + secrets.token_hex(32) + '\n')
PY
```

La commande refuse d'écraser une clé existante. Dans ce même terminal, charger ensuite la clé et lancer Jupyter :

```bash
set -a
. ./.env
set +a
jupyter notebook atelier_jour3.ipynb
```

Dans Jupyter, choisir le noyau du nouvel environnement. Une nouvelle clé crée de nouveaux pseudonymes : conserver la clé d'origine de façon sûre si les exports doivent rester comparables. Ne jamais envoyer la clé avec les livrables.

Les fichiers de `data/` et `.env` sont ignorés par Git. Pour rendre les deux Parquet lorsqu'ils sont demandés, les fournir séparément par un canal adapté, sans joindre `.env`. Les données pseudonymisées restent à protéger.

## Ancien site de découverte MongoDB

Le site initial permet toujours d'explorer les collections fictives et les analyses locales :

```bash
docker start mongo
../jour-2/venv/bin/python dashboard.py
```

Il est accessible sur **http://127.0.0.1:8050/**. Il lit directement les données brutes de MongoDB et affiche certains identifiants ; ce n'est pas le dashboard pseudonymisé du TP3. Les mots de passe et plusieurs champs sensibles y sont masqués. Ce serveur écoute uniquement en local et ne modifie pas MongoDB.

## Comprendre les chiffres

- Montant commandé : somme des lignes de produits après réduction, tous statuts confondus.
- Montant encaissé : somme des paiements `PAID` uniquement.
- Paniers analysés : nombre de paiements conservés après vérification d'un paiement unique par panier.
- Taux d'acceptation : paiements `PAID` divisés par tous les paiements analysés.

Les dates sont simulées. Dans le TP2, la date du paiement est la date la plus ancienne du panier : l'évolution mensuelle ne représente pas un historique réel. Le jeu de données ne précise pas de devise.

## Vérifier

Depuis `jour-3`, avec l'environnement du TP2 activé :

```bash
python -m unittest discover -s tests -v
```
