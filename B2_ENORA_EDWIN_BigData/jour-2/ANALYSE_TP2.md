# TP2 — Analyse des résultats

**Binôme : Enora et Edwin**

Projet BigData Commerce Analytics — exécution du 26 novembre 2026

## Données et paiements simulés

Le fichier du jour 1 contient 800 lignes de produits correspondant à 208 paniers. La simulation crée une seule tentative de paiement par panier, avec une graine fixée à 42. Les probabilités demandées sont de 70 % pour `PAID`, 20 % pour `REFUSED` et 10 % pour `PENDING` ; le résultat d'un tirage ne donne pas forcément ces proportions exactement.

| Statut | Nombre | Proportion | Montant associé |
| --- | ---: | ---: | ---: |
| PAID | 150 | 72,12 % | 2 669 235,61 |
| REFUSED | 37 | 17,79 % | 423 555,75 |
| PENDING | 21 | 10,10 % | 363 918,22 |
| **Total** | **208** | **100 %** | **3 456 709,58** |

Le montant réellement encaissé dans cette simulation est **2 669 235,61**, car seuls les paiements `PAID` sont acceptés. Les paiements refusés et en attente ne sont pas encaissés. Les sommes sont exprimées dans l'unité monétaire des données ; le sujet ne précise pas de devise.

L'index unique sur `cart_id`, le nombre de paiements et la comparaison des identifiants avec les commandes permettent de vérifier qu'aucun panier n'est compté plusieurs fois. La somme des paiements acceptés correspond au total encaissé calculé par catégorie et au total calculé par mois.

## Indicateurs

- La catégorie `vehicle` a le montant commandé le plus élevé : **1 682 064,05**. Son montant encaissé est de **1 374 964,95**. Le montant commandé par catégorie inclut toutes les lignes ; l'encaissé ne retient que les paniers payés.
- Le client fictif `user_id = 30` arrive en tête des montants encaissés avec **155 507,16**.
- Le taux de refus est de **37 / 208 = 17,79 %**.
- Le mois simulé dont le montant encaissé est le plus élevé est **janvier 2025**, avec **977 810,05**.

Les quatre tableaux complets sont disponibles dans le dossier [resultats](resultats/) pour les visualisations du jour 3.

**Limite sur les dates :** 207 paniers ont plusieurs valeurs `order_date` sur leurs lignes. Ces dates sont synthétiques ; nous avons retenu la date la plus ancienne de chaque panier pour y rattacher son paiement. Ce choix facilite l'exercice, mais peut déplacer les montants vers les premiers mois : l'évolution mensuelle ne représente donc pas un historique réel des paiements.

## Spark et lazy evaluation

Un DataFrame Spark décrit des données à traiter. Des transformations comme `select`, `filter`, `withColumn` et `groupBy` construisent un plan ; elles ne déclenchent pas à elles seules le calcul complet. Dans le notebook, le nombre de jobs affichés ne change pas quand on construit le plan ; après l'action `show()`, de nouveaux jobs apparaissent dans Spark UI. C'est la *lazy evaluation* : Spark exécute le plan quand une action demande un résultat.

La lecture MongoDB utilise une partition dans notre exécution. Après `repartition(4)`, nous observons quatre partitions de 200 lignes. Une Task traite une partition dans un Stage ; un Job peut comporter plusieurs Stages, notamment lorsqu'un échange de données est nécessaire. Les captures montrent les [Jobs](captures/spark_ui_jobs.png) et le [détail d'un Stage et de ses Tasks](captures/spark_ui_stage_tasks.png). Sur cette dernière, le Stage 103 du Job 57 comporte 16 Tasks terminées avec succès et aucune Task échouée.

Dans [SQL / DataFrame](captures/spark_ui_sql.png), nous observons 21 requêtes terminées, dont des actions `count`, `show` et `collect`. L'onglet [Executors](captures/spark_ui_executors.png) montre un `driver` local disposant de 16 cœurs et ayant terminé 91 Tasks au moment de la capture. L'onglet [Environment](captures/spark_ui_environment.png) confirme Java 17 ; les propriétés relevées dans le notebook indiquent aussi le mode `local[*]` et quatre partitions de shuffle.

Ces mesures concernent un petit jeu de données exécuté sur un seul poste : elles ne permettent pas de conclure sur les performances d'un cluster de production.
