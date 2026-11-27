# Commerce Analytics - Jour 3

## Sécurité, analyse et tableau de bord

Projet fil rouge Big Data - B2 Sup de Vinci - Enora et Edwin

Ce document accompagne le notebook et la démonstration du jour 3. Le projet utilise des données simulées : les résultats servent à expliquer une méthode et ne représentent pas l'activité d'un véritable commerce.

## 1. Objectif et architecture

L'objectif est de reprendre les données déjà préparées, de protéger les identifiants clients et de rendre les indicateurs faciles à comprendre. La collecte et l'ingestion ont été réalisées les jours précédents : elles ne sont pas relancées dans le TP3.

```text
DummyJSON / CSV
      |
      v
Python - collecte et ingestion
      |
      v
MongoDB - collections sources
      |-- PySpark - indicateurs du jour 2 -----> comparaison
      |
      +-- Pandas + HMAC - préparation du jour 3
               |
               v
        Parquet pseudonymisés
               |-- Matplotlib - trois graphiques
               +-- Streamlit et Plotly - tableau de bord
```

- **DummyJSON et CSV** : sources des données fictives et fichiers préparés au jour 1.
- **Python et MongoDB** : ingestion et conservation des données dans des collections au jour 2.
- **PySpark** : calcul des indicateurs du jour 2 en mode local sur cet ordinateur ; ses résultats sont utilisés pour vérifier les analyses du jour 3. Spark permet aussi des traitements distribués sur plusieurs machines.
- **Pandas et HMAC** : lecture de MongoDB, nettoyage des colonnes et remplacement des identifiants clients.
- **Parquet, Matplotlib et Streamlit** : stockage des données analytiques, graphiques et exploration interactive.

Le notebook du jour 3 lit les collections MongoDB et compare ensuite ses calculs aux résultats PySpark. Il ne lit pas les fichiers PySpark pour créer les Parquet.

<!-- PAGE -->

## 2. Préparer et protéger les données

Les collections utilisées sont `commerce.raw_commandes` et `commerce.raw_payments`. Les champs français des paiements sont renommés dans Pandas : `montant` devient `amount`, `statut` devient `payment_status` et `date_paiement` devient `payment_date`. La base MongoDB n'est pas modifiée.

Les montants sont convertis en nombres et les dates en dates. Les valeurs invalides deviennent manquantes et les lignes inutilisables sont écartées ; le notebook indique combien ont été conservées et écartées. Sur ce jeu, les 800 lignes de commandes et les 208 paiements ont été conservés.

### Pseudonymisation

La fonction HMAC-SHA-256 combine `user_id` avec une clé secrète. Avec une même clé, le même client reçoit toujours le même pseudonyme dans les commandes et les paiements. Cela permet de calculer un total par client sans afficher directement son identifiant.

Les exports ne gardent que le pseudonyme, la catégorie, le montant et la date pour les commandes ; le pseudonyme, le montant, le statut et la date pour les paiements. Ils ne contiennent ni la clé ni les identifiants directs.

### Risques et précautions

- Pseudonymiser ne veut pas dire anonymiser : les lignes d'un même client restent reliables et des recoupements peuvent permettre de l'identifier.
- Une personne qui possède la clé et connaît des identifiants peut recalculer les pseudonymes. La clé reste dans une variable d'environnement ; le fichier local `.env` est ignoré par Git et accessible uniquement à son propriétaire.
- Les fichiers Parquet restent à protéger : limiter les accès, les partages et la durée de conservation au nécessaire. La base source et les anciens résultats du jour 2 contiennent encore des identifiants.
- Le notebook montre trois correspondances fictives pour expliquer le principe, comme demandé dans le sujet. Avec des données réelles, il faudrait retirer ces exemples avant tout partage.
- MongoDB est utilisé ici en local, avec une démonstration sans authentification ; il ne faut pas exposer ce service sur Internet.

<!-- PAGE -->

## 3. Résultats et règles de calcul

Dans les données disponibles, 208 paiements correspondent à 208 paniers distincts : le notebook vérifie l'unicité du panier pour chaque paiement avant de compter les paniers analysés. Aucun paiement ni ligne de commande n'a été écarté lors du nettoyage.

- **Montant commandé : 3 456 709,58.** Somme de `discounted_line_total` pour les 800 lignes de produits, quel que soit le statut du paiement.
- **Montant encaissé : 2 669 235,61.** Somme du montant des 150 paiements `PAID` uniquement.
- **Taux d'acceptation : 72,12 %.** 150 paiements acceptés divisés par 208 paiements analysés.
- **Taux de refus : 17,79 %.** 37 paiements refusés divisés par 208 paiements analysés ; 21 paiements sont en attente.

Le montant commandé et le montant encaissé ne désignent pas la même chose : tous les paniers ne sont pas payés. Il ne faut pas additionner `cart_discounted_total` sur les lignes de produits, car le total du panier y est répété. La devise n'est pas indiquée dans le jeu de données.

### Ce qu'on peut dire à l'oral

« Nous commençons par distinguer ce que les clients ont commandé de ce qui a réellement été encaissé dans notre simulation. Sur 208 paiements, 150 sont acceptés et 37 refusés. Les autres sont en attente. Les montants encaissés ne retiennent donc que les paiements acceptés. »

Les résultats Pandas ont été comparés aux exports PySpark du jour 2 pour les catégories, les mois et le Top 10 clients. Pour cette dernière comparaison, les identifiants du jour 2 sont pseudonymisés en mémoire avec la même clé.

<!-- PAGE -->

## 4. Graphique - montant commandé par catégorie

Le graphique additionne le montant de chaque ligne de produit après réduction. Il présente toutes les catégories, avec des barres horizontales pour faciliter la lecture.

<!-- IMAGE:figures/ca_par_categorie.png -->

**Interprétation :** la catégorie `vehicle` arrive en tête avec 1 682 064,05 commandés, devant `motorcycle` et `mens-watches`. Il s'agit du montant commandé, pas nécessairement encaissé.

<!-- PAGE -->

## 5. Graphiques - temps et clients

### Évolution mensuelle des encaissements

La courbe additionne uniquement les paiements `PAID`, regroupés par mois de paiement. Janvier 2025 est le mois le plus élevé dans ces données, avec 977 810,05 encaissés.

<!-- IMAGE:figures/evolution_mensuelle.png -->

Les dates sont simulées. Certaines lignes d'un panier ont des dates différentes : au TP2, la date du paiement a été fixée à la date la plus ancienne du panier. Cette courbe montre donc le traitement, pas un historique réel.

<!-- PAGE -->

### Top 10 des clients pseudonymisés

Les paiements acceptés sont regroupés par pseudonyme. Le premier client du classement totalise 155 507,16. Le graphique affiche un extrait du pseudonyme pour rester lisible ; le calcul utilise le pseudonyme complet.

<!-- IMAGE:figures/top_10_clients.png -->

Dans le tableau de bord, les graphiques Plotly sont interactifs. Les vues permettent de parcourir les catégories, les paiements, les clients et les deux jeux de données pseudonymisés.

<!-- PAGE -->

## 6. Trame pour la présentation orale

1. **Le besoin.** Présenter l'objectif : transformer des données de commerce simulées en indicateurs utiles.
2. **Les sources.** Expliquer DummyJSON et les CSV, puis l'ingestion Python dans MongoDB pendant les deux premiers jours.
3. **Le calcul.** Montrer les résultats PySpark du TP2 ; distinguer le commandé de l'encaissé et expliquer le statut `PAID`.
4. **La sécurité.** Montrer la fonction HMAC, expliquer pourquoi le pseudonyme reste stable et pourquoi la clé doit rester privée.
5. **La préparation.** Présenter la conversion des montants et dates, puis les deux fichiers Parquet sans identifiants directs.
6. **Les résultats.** Montrer les trois graphiques et donner une observation pour chacun : catégorie dominante, mois le plus élevé et classement pseudonymisé.
7. **Le dashboard.** Ouvrir les vues interactives, explorer un tableau et rappeler les limites des dates fictives.

### Questions possibles

**Pourquoi les deux montants sont-ils différents ?** Les commandes couvrent les paniers analysés ; seuls les paiements acceptés sont comptés comme encaissés.

**Le pseudonyme rend-il les données anonymes ?** Non. Il permet toujours de relier les lignes d'un même client, et des recoupements peuvent réidentifier une personne.

**Pourquoi utiliser Parquet ?** Ce format en colonnes conserve les types des données et se prête aux analyses. Le dashboard peut lire ces fichiers sans accéder directement à MongoDB.

**Pourquoi la courbe mensuelle a-t-elle une limite ?** Les dates sont simulées et la date de paiement est calculée à partir de la date la plus ancienne du panier.

Pour démarrer le notebook et le dashboard, suivre le fichier `README.md` du dossier `jour-3`.
