# Démarrer le TP2

L'environnement de ce TP est installé dans le dossier `jour-2/venv`. Le conteneur MongoDB s'appelle `mongo` et écoute sur `127.0.0.1:27017`.

## Lancer le TP

Ouvrir un terminal dans le dossier `jour-2`, puis exécuter :

```bash
source venv/bin/activate
export JAVA_HOME="$VIRTUAL_ENV/jdk-17"
docker start mongo
jupyter notebook
```

Garder le terminal ouvert pendant le travail. Dans Jupyter, sélectionner le noyau **Python (TP2 Big Data)** pour les notebooks du jour 2.

Conserver le conteneur `mongo` pour retrouver les données au jour 3. Après un arrêt, `docker start mongo` le redémarre avec ses données.

Pour vérifier les versions depuis le terminal avant de lancer Jupyter :

```bash
java -version
javac -version
python -c "import pyspark; print(pyspark.__version__)"
```

Java doit afficher une version 17 et PySpark la version 4.0.1.

## Vérifier MongoDB dans un notebook

```python
from pymongo import MongoClient

client = MongoClient("mongodb://127.0.0.1:27017")
print(client.admin.command("ping"))
```

Le résultat attendu est `{'ok': 1.0}`. La base demandée par le sujet se sélectionne avec `client["commerce"]`.

## Démarrer Spark dans le deuxième notebook

```python
import os
import sys
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("BigData Commerce Analytics")
    .config("spark.jars.ivy", os.path.join(sys.prefix, ".ivy2"))
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.13:11.1.0")
    .config("spark.mongodb.read.connection.uri", "mongodb://127.0.0.1:27017")
    .getOrCreate()
)

print("Spark :", spark.version)
print("Spark UI :", spark.sparkContext.uiWebUrl)
```

Ouvrir l'adresse affichée pour accéder à Spark UI pendant que la session Spark est active. Le [connecteur MongoDB 11.1](https://www.mongodb.com/docs/spark-connector/current/) est compatible avec Spark 4.

## Données et travail à réaliser

Si les notebooks sont placés directement dans `jour-2`, le fichier de commandes du jour 1 est accessible avec le chemin :

```text
../jour-1/data/processed/commandes_ecommerce.csv
```

Les deux notebooks sont dans `jour-2` :

1. `01_ingestion_api_mongodb.ipynb` collecte les ressources, importe les commandes et simule les paiements.
2. `02_traitement_pyspark.ipynb` lit MongoDB, étudie Spark et calcule les indicateurs.

Ils ont déjà été exécutés et contiennent leurs résultats. Pour les relancer, exécuter d'abord le notebook 01, puis le notebook 02. Les captures Spark UI sont dans `captures/`, les données préparées pour le jour 3 dans `resultats/` et la synthèse dans `ANALYSE_TP2.md`.
