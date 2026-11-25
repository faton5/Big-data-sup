# Synthèse — Atelier 1 : exploration des sources (DummyJSON)
**Binôme : Enora & Enora**
Collecte du 25/11/2026 · API de démonstration, données fictives

## Inventaire des ressources
| Ressource | Endpoint | Volume | Rôle |
|---|---|---|---|
| products | /products | 194 | Catalogue (24 catégories) |
| carts | /carts | 208 (800 lignes produits) | Paniers, JSON imbriqué |
| users | /users | 208 (52 colonnes à plat) | Profils clients |
| comments | /comments | 340 | Commentaires liés aux posts |
| posts | /posts | 251 | Hors e-commerce |
| recipes | /recipes | 50 | Hors e-commerce |
| quotes | /quotes | 1 454 | Hors e-commerce (la plus volumineuse) |
| todos | /todos | 254 | Hors e-commerce |

Liens : `carts.userId = users.id` et `carts.products[].id = products.id`.

## Évaluation des 5V
| V | Niveau | Preuve |
|---|---|---|
| Volume | Faible | Environ 1,7 Mo, de 50 à 1 454 enregistrements par ressource |
| Vitesse | Faible | Instantané à la demande, pas de date de transaction : pas du temps réel |
| Variété | Moyen | JSON imbriqué, 52 colonnes pour `users`, 8 types de ressources |
| Véracité | Faible | Données fictives, `brand` absente pour 47 % des produits, 12 doublons dans les lignes de panier |
| Valeur | Moyen | Utile pour apprendre à analyser paniers, catégories et prix, mais sans valeur de décision réelle |

## Usages et limites des sources principales
- **Produits** : répartition des prix et des catégories, catalogue de référence. Limites : données fictives, marque souvent absente.
- **Paniers** : paniers volumineux, effet des remises. Limites : ce ne sont pas des commandes finalisées, et il n'y a pas de date fiable.
- **Utilisateurs** : segmentation illustrative, lien panier ↔ client. Limites : champs sensibles (mot de passe, ssn, banque) à écarter, données très imbriquées.
- **Commentaires** : analyse de texte et d'engagement. Limites : liés aux publications et non aux produits, textes génériques.

## Conclusion
Je conserverais `products`, `carts` et `users`, car elles sont reliées entre elles et suffisent pour un cas e-commerce. Je laisserais de côté `posts`, `recipes`, `quotes` et `todos`, qui n'ont aucun lien avec des achats. Le point faible principal est la véracité : tout est fictif, sans vraies commandes ni dates. Ces données servent donc à s'entraîner (aplatir, contrôler, nettoyer) et pas à prendre de vraies décisions.

## Pour l'oral (3 minutes)
- **Source présentée :** `carts`.
- **V dominant :** la variété (JSON imbriqué à aplatir).
- **Opportunité :** analyser les paniers et les remises.
- **Limite importante :** un panier n'est pas une commande finalisée.
