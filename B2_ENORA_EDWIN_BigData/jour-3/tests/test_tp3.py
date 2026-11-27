import ast
import hashlib
import hmac
import re
import secrets
import unittest
from collections import Counter
from pathlib import Path

import nbformat
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import PyMongoError


RACINE = Path(__file__).resolve().parents[1]
NOTEBOOK = RACINE / "atelier_jour3.ipynb"
COMMANDES = RACINE / "data" / "commandes_pseudonymisees.parquet"
PAIEMENTS = RACINE / "data" / "paiements_pseudonymises.parquet"


def fonction_du_notebook():
    if not NOTEBOOK.exists():
        return None
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    for cellule in notebook.cells:
        if cellule.cell_type != "code":
            continue
        arbre = ast.parse(cellule.source)
        fonctions = [noeud for noeud in arbre.body if isinstance(noeud, ast.FunctionDef) and noeud.name == "pseudonymiser"]
        if fonctions:
            module = ast.Module(body=fonctions, type_ignores=[])
            espace = {"hmac": hmac, "hashlib": hashlib}
            exec(compile(module, str(NOTEBOOK), "exec"), espace)
            return espace["pseudonymiser"]
    return None


class PseudonymisationTest(unittest.TestCase):
    def test_hmac_stable_et_depend_de_la_cle_et_de_l_identifiant(self):
        fonction = fonction_du_notebook()
        self.assertIsNotNone(fonction, "Le notebook doit définir pseudonymiser")
        cle = secrets.token_hex(32)
        autre_cle = secrets.token_hex(32)
        valeur = fonction(17, cle)
        attendu = hmac.new(cle.encode("utf-8"), b"17", hashlib.sha256).hexdigest()
        self.assertEqual(valeur, attendu)
        self.assertEqual(valeur, fonction(17, cle))
        self.assertNotEqual(valeur, fonction(18, cle))
        self.assertNotEqual(valeur, fonction(17, autre_cle))
        self.assertRegex(valeur, r"^[0-9a-f]{64}$")

    def test_notebook_execute_sans_erreur(self):
        self.assertTrue(NOTEBOOK.exists(), "Le notebook du jour 3 doit exister")
        notebook = nbformat.read(NOTEBOOK, as_version=4)
        nbformat.validate(notebook)
        cellules = [cellule for cellule in notebook.cells if cellule.cell_type == "code"]
        self.assertTrue(cellules)
        self.assertTrue(all(cellule.execution_count is not None for cellule in cellules))
        erreurs = [sortie for cellule in cellules for sortie in cellule.outputs if sortie.output_type == "error"]
        self.assertEqual(erreurs, [])

    def test_exports_sans_identifiants_directs(self):
        self.assertTrue(COMMANDES.exists(), "Le Parquet des commandes doit exister")
        self.assertTrue(PAIEMENTS.exists(), "Le Parquet des paiements doit exister")
        commandes = pd.read_parquet(COMMANDES)
        paiements = pd.read_parquet(PAIEMENTS)
        self.assertEqual(set(commandes.columns), {"user_id_pseudo", "category", "discounted_line_total", "order_date"})
        self.assertEqual(set(paiements.columns), {"user_id_pseudo", "amount", "payment_status", "payment_date"})
        self.assertEqual(len(commandes), 800)
        self.assertEqual(len(paiements), 208)
        self.assertTrue(commandes.user_id_pseudo.str.fullmatch(r"[0-9a-f]{64}").all())
        self.assertTrue(paiements.user_id_pseudo.str.fullmatch(r"[0-9a-f]{64}").all())
        self.assertFalse(commandes.order_date.isna().any())
        self.assertFalse(paiements.payment_date.isna().any())
        self.assertAlmostEqual(paiements.loc[paiements.payment_status == "PAID", "amount"].sum(), 2669235.61, places=2)

    def test_meme_pseudonyme_dans_les_deux_sources(self):
        self.assertTrue(COMMANDES.exists() and PAIEMENTS.exists(), "Les Parquet doivent être créés")
        fichier_cle = RACINE / ".env"
        if not fichier_cle.exists():
            self.skipTest("La clé locale est nécessaire pour comparer les sources")
        cle = next(ligne.split("=", 1)[1] for ligne in fichier_cle.read_text().splitlines() if ligne.startswith("PSEUDO_KEY="))
        self.assertFalse(cle in NOTEBOOK.read_text(), "La clé ne doit pas figurer dans le notebook")
        client = MongoClient("mongodb://127.0.0.1:27017", serverSelectionTimeoutMS=500)
        try:
            client.admin.command("ping")
            sources = [
                (client.commerce.raw_commandes, pd.read_parquet(COMMANDES)),
                (client.commerce.raw_payments, pd.read_parquet(PAIEMENTS)),
            ]
            for collection, export in sources:
                attendus = Counter(
                    hmac.new(cle.encode("utf-8"), str(document["user_id"]).encode("utf-8"), hashlib.sha256).hexdigest()
                    for document in collection.find({}, {"_id": 0, "user_id": 1})
                )
                self.assertEqual(attendus, Counter(export.user_id_pseudo))
        except PyMongoError:
            self.skipTest("MongoDB indisponible")
        finally:
            client.close()

    def test_les_trois_graphes_sont_exports(self):
        for nom in ["ca_par_categorie.png", "evolution_mensuelle.png", "top_10_clients.png"]:
            fichier = RACINE / "figures" / nom
            self.assertTrue(fichier.is_file() and fichier.stat().st_size > 1000, f"Graphique manquant : {nom}")


if __name__ == "__main__":
    unittest.main()
