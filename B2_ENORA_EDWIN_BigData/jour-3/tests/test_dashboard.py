import importlib.util
import unittest
from pathlib import Path

from pymongo import MongoClient
from pymongo.errors import PyMongoError


MODULE = Path(__file__).resolve().parents[1] / "dashboard.py"


def charger_dashboard():
    if not MODULE.exists():
        return None
    spec = importlib.util.spec_from_file_location("dashboard", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CalculsDashboardTest(unittest.TestCase):
    def setUp(self):
        self.dashboard = charger_dashboard()
        self.assertIsNotNone(self.dashboard, "Le module du tableau de bord doit exister")
        self.commandes = [
            {"cart_id": 1, "category": "tech", "discounted_line_total": 70, "order_date": "2025-01-01"},
            {"cart_id": 1, "category": "maison", "discounted_line_total": 30, "order_date": "2025-01-02"},
            {"cart_id": 2, "category": "tech", "discounted_line_total": 80, "order_date": "2025-01-03"},
            {"cart_id": 3, "category": "maison", "discounted_line_total": 40, "order_date": "2025-02-01"},
            {"cart_id": 4, "category": "maison", "discounted_line_total": 10, "order_date": "2025-02-02"},
        ]
        self.paiements = [
            {"cart_id": 1, "user_id": 7, "montant": 100, "statut": "PAID", "date_paiement": "2025-01-01"},
            {"cart_id": 2, "user_id": 7, "montant": 80, "statut": "REFUSED", "date_paiement": "2025-01-03"},
            {"cart_id": 3, "user_id": 9, "montant": 40, "statut": "PAID", "date_paiement": "2025-02-01"},
            {"cart_id": 4, "user_id": 10, "montant": 10, "statut": "PENDING", "date_paiement": "2025-02-02"},
        ]

    def test_les_montants_encaisses_excluent_les_paiements_non_acceptes(self):
        resultat = self.dashboard.analyser(self.commandes, self.paiements)
        self.assertEqual(resultat["lignes_commandes"], 5)
        self.assertEqual(resultat["paniers"], 4)
        self.assertEqual(resultat["paiements"], 4)
        self.assertEqual(resultat["encaisse"], 140)
        self.assertEqual(resultat["taux_refus"], 25)
        categories = {row["nom"]: row for row in resultat["categories"]}
        self.assertEqual(categories["tech"]["commande"], 150)
        self.assertEqual(categories["tech"]["encaisse"], 70)
        self.assertEqual(categories["maison"]["commande"], 80)
        self.assertEqual(categories["maison"]["encaisse"], 70)

    def test_clients_et_mois_utilisent_les_paiements_acceptes(self):
        resultat = self.dashboard.analyser(self.commandes, self.paiements)
        self.assertEqual(resultat["top_clients"], [{"user_id": 7, "montant": 100}, {"user_id": 9, "montant": 40}])
        self.assertEqual(resultat["mensuel"], [{"mois": "2025-01", "montant": 100}, {"mois": "2025-02", "montant": 40}])
        self.assertEqual(resultat["paniers_dates_multiples"], 1)

    def test_base_vide_sans_division_par_zero(self):
        resultat = self.dashboard.analyser([], [])
        self.assertEqual(resultat["encaisse"], 0)
        self.assertEqual(resultat["taux_refus"], 0)
        self.assertEqual(resultat["categories"], [])

    def test_clients_a_egalite_tries_par_identifiant_numerique(self):
        paiements = [
            {"cart_id": 1, "user_id": 10, "montant": 50, "statut": "PAID", "date_paiement": "2025-01-01"},
            {"cart_id": 2, "user_id": 2, "montant": 50, "statut": "PAID", "date_paiement": "2025-01-01"},
        ]
        resultat = self.dashboard.analyser([], paiements)
        self.assertEqual([row["user_id"] for row in resultat["top_clients"]], [2, 10])

    def test_les_champs_sensibles_sont_masques_meme_imbriques(self):
        document = {
            "firstName": "Alex",
            "password": "secret",
            "email": "alex@example.test",
            "birthDate": "1990-01-01",
            "bloodGroup": "AB+",
            "address": {"address": "12 rue Exemple", "city": "Rennes", "coordinates": {"lat": 48.1, "lng": -1.6}},
            "bank": {"iban": "FR123", "cardNumber": "1234", "cardExpire": "12/30"},
            "crypto": [{"wallet": "abcdef"}],
        }
        propre = self.dashboard.nettoyer_document(document)
        self.assertEqual(propre["firstName"], "Alex")
        self.assertNotIn("secret", str(propre))
        self.assertNotIn("alex@example.test", str(propre))
        self.assertNotIn("FR123", str(propre))
        self.assertNotIn("1234", str(propre))
        self.assertNotIn("abcdef", str(propre))
        self.assertNotIn("1990-01-01", str(propre))
        self.assertNotIn("AB+", str(propre))
        self.assertNotIn("12 rue Exemple", str(propre))
        self.assertNotIn("48.1", str(propre))
        self.assertNotIn("12/30", str(propre))
        self.assertEqual(propre["address"]["city"], "Rennes")


class RechercheMongoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = charger_dashboard()
        cls.client = MongoClient("mongodb://127.0.0.1:27017", serverSelectionTimeoutMS=500)
        try:
            cls.client.admin.command("ping")
        except PyMongoError:
            cls.client.close()
            raise unittest.SkipTest("MongoDB indisponible pour la recherche")

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_la_recherche_trouve_les_valeurs_affichees(self):
        exemples = [("raw_quotes", "author"), ("raw_recipes", "cuisine"), ("raw_recipes", "difficulty")]
        for collection, champ in exemples:
            with self.subTest(collection=collection, champ=champ):
                documents = self.client.commerce[collection]
                exemple = documents.find_one({champ: {"$type": "string"}})
                if exemple is None:
                    self.skipTest(f"Aucun document disponible dans {collection}")
                recherche = self.dashboard.construire_recherche(exemple[champ])
                self.assertGreater(documents.count_documents(recherche), 0)

    def test_la_recherche_comprend_un_etat_termine(self):
        collection = self.client.commerce.raw_todos
        if collection.count_documents({"completed": True}) == 0:
            self.skipTest("Aucune tâche terminée disponible")
        self.assertGreater(collection.count_documents(self.dashboard.construire_recherche("oui")), 0)


if __name__ == "__main__":
    unittest.main()
