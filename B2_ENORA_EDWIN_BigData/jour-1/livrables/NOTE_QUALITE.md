# Note de qualité — table `commandes_ecommerce.csv`
**Binôme : Enora & Edwin**
**Atelier 2 · BigData Commerce Analytics (DummyJSON)**
Source : https://dummyjson.com (carts, products, users) · Collecte du 25/11/2026

## 1. Dimensions
800 lignes × 16 colonnes. 208 paniers, 189 produits, 208 utilisateurs.

## 2. Granularité
Une ligne = **un produit dans un panier** (ligne de panier). Ce n'est ni une commande finalisée, ni un panier entier : un panier compte jusqu'à 6 lignes. Chaque panier correspond à un utilisateur distinct (208 paniers, 208 utilisateurs).

## 3. Types à corriger
- `order_date` est lue comme texte : conversion en `datetime`.
- Les champs numériques (`quantity`, prix, totaux, remise) sont déjà corrects, mais ils sont convertis explicitement par sécurité.
- Les identifiants (`cart_id`, `user_id`, `product_id`) sont des entiers : OK.

## 4. Valeurs manquantes et doublons
- Valeurs manquantes : une seule colonne, `brand` (377 lignes, 47,12 %). Ce n'est pas une erreur : beaucoup de produits n'ont pas de marque dans l'API.
- Doublons exacts : 0.
- Doublons sur la clé métier `cart_id + product_id` : 12 lignes (un même produit apparaît deux fois dans un panier).

## 5. Anomalies et limites observées
1. **Valeurs extrêmes de prix** : `unit_price` va de 0,79 à 36 999,99 (moyenne 1 559, médiane 35). La catégorie `vehicle` pèse à elle seule environ 1,88 M sur le total des lignes. Ces valeurs sont légitimes (véhicules, montres), mais elles faussent les moyennes et les graphiques.
2. **`cart_total` est répété sur chaque ligne d'un même panier** : l'additionner ligne par ligne gonfle le chiffre d'affaires.
3. **`order_date` est synthétique** : elle est générée pour le TP et ne vient pas de l'API. Aucune tendance temporelle réelle ne peut en être tirée.
4. **Données fictives** : DummyJSON est une API de démonstration, ces paniers ne sont pas de vraies ventes.
5. Les contrôles métier ne révèlent aucune incohérence (voir ci-dessous).

## 6. Contrôles de cohérence métier (0 anomalie)
| Contrôle | Anomalies |
|---|---|
| Quantité ≤ 0 | 0 |
| Prix négatif | 0 |
| Remise hors 0–100 % | 0 |
| `line_total` ≠ quantité × prix (> 1 centime) | 0 |
| Total remisé > total initial | 0 |

## 7. Règles de nettoyage retenues
- Supprimer les lignes avec `quantity` manquante ou ≤ 0 (0 ligne concernée).
- Supprimer les lignes avec `unit_price` manquant ou < 0 (0 ligne concernée).
- Dédoublonner sur `cart_id + product_id`, en gardant la première ligne (12 lignes supprimées).
- Ne pas remplir `brand` avec une valeur fictive : on la garde vide.
- Résultat : 800 → **788 lignes**. Le fichier brut reste intact. Résultat enregistré dans `data/processed/commandes_ecommerce_nettoyees.csv`.

> Remarque : garder la première ligne d'un doublon `cart_id + product_id` perd la quantité de la seconde. Une alternative plus fidèle serait de les fusionner en additionnant les quantités.

## 8. Précautions avant MongoDB ou Spark
- Conserver `brand` vide comme `null`, et ne pas écrire la chaîne « inconnu ».
- Ne jamais additionner `cart_total` ou `cart_discounted_total` par ligne : agréger au niveau panier (`cart_id`).
- Convertir `order_date` en vrai type date au chargement.
- Les données utilisateur (`username`) sont fictives, mais il faut les traiter comme des données personnelles potentielles dans un cas réel.
- Les valeurs extrêmes de prix demandent une analyse par catégorie (médiane plutôt que moyenne).
- Dans MongoDB, un panier peut être un document avec un tableau de produits imbriqués, ce qui évite la répétition de `cart_total`.

## Réponses aux questions de réflexion
- **Pourquoi garder une copie brute ?** Pour pouvoir revenir en arrière, vérifier ce que le nettoyage a changé, et refaire le traitement si une règle change.
- **Pourquoi `cart_total` ne doit-il pas être additionné par ligne ?** Parce que sa valeur est répétée sur chaque ligne du même panier : on le compterait plusieurs fois.
- **Qualité technique ou pertinence métier ?** La qualité technique vérifie que les données sont propres (types, manquants, doublons). La pertinence métier vérifie qu'elles sont utiles et représentatives. Ici elles sont propres mais fictives, donc peu pertinentes pour de vraies décisions.
