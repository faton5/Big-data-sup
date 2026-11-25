# Atelier 3 — Cadrage des 5V du projet BigData Commerce Analytics
**Binôme : Enora & Enora** · B2 · Sup de Vinci Rennes · Jour 1 · données collectées le 25/11/2026

## Chaîne du projet
Sources (API / CSV) → Collecte Python → Stockage MongoDB (jour 2) → Traitement Spark (jour 2) → Analyse et visualisation (jour 3).

## Les 5V du projet
| V | Questions | Réponse pour notre projet | Niveau |
|---|---|---|---|
| **Volume** | Combien de commandes et d'événements par jour ? Quelle croissance ? | **Observé** : 208 paniers, 800 lignes de panier, 194 produits, 208 utilisateurs (environ 1,7 Mo de JSON) : un instantané, pas de flux quotidien. **Estimation pour une vraie boutique (hypothèse du cours)** : 10 000 commandes par jour, soit environ 3,6 millions par an, et environ 50 000 événements par jour (5 par commande) avant les clics et recherches. La croissance n'est pas mesurable avec DummyJSON. | Faible (observé), élevé (cible) |
| **Vitesse** | Quelles données en temps réel, lesquelles par lots ? | **Temps réel** : détection de fraude (réaction en secondes), clics et recherches pour la recommandation. **Par lots** : rapports de ventes nocturnes, nettoyage et profilage (notre atelier 2), prévision des stocks. Dans le projet, tout est en lots : l'API est interrogée à la demande. | Faible (observé) |
| **Variété** | Quelles sources et formats intégrer ? | API JSON (products, carts, users, comments), CSV (`commandes_ecommerce.csv`), JSON imbriqué (panier → produits, utilisateur → adresse, banque). Sources possibles à ajouter : logs de navigation, avis clients en texte libre, paiements. Types : structurées (CSV commandes), semi-structurées (JSON des paniers), non structurées (avis). | Moyen |
| **Véracité** | Quels problèmes relevés dans l'atelier 2 ? | 1) `brand` absente sur 47 % des lignes (377 sur 800). 2) 12 doublons sur `cart_id + product_id`. 3) Prix très dispersés (0,79 à 36 999,99, médiane 35) et `cart_total` répété sur chaque ligne. S'y ajoutent : `order_date` synthétique et données fictives. Aucune incohérence de calcul (quantité, remise, totaux). | Faible à moyen |
| **Valeur** | Quelles décisions améliorer ? | Recommandation de produits (paniers + catégories), détection de fraude, prévision des stocks. Sur nos données fictives, la valeur est pédagogique : apprendre la chaîne complète, pas décider. | Moyen |

## Comparaison avec l'estimation de l'atelier 1
Atelier 1 : 208 paniers et 194 produits annoncés par l'API. Atelier 2 : 800 lignes de panier pour 208 paniers (environ 3,8 lignes par panier) et 189 produits distincts achetés. Les deux ateliers sont cohérents entre eux.

## Risques et précautions pour les jours 2 et 3
- **MongoDB** : stocker un panier comme un document avec ses produits imbriqués, conserver `brand` vide en `null`.
- **Spark** : agréger `cart_total` au niveau du panier (jamais ligne par ligne).
- **Sécurité (jour 3)** : écarter les champs sensibles de `users` (password, ssn, bank, ip) et appliquer le RGPD si les données étaient réelles.
- **Biais de popularité** pour toute recommandation, et caractère fictif des données à rappeler dans la restitution.
