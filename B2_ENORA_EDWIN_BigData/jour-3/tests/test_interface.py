import json
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


APPLICATION = Path(__file__).resolve().parents[1] / "app_streamlit.py"


class InterfaceTest(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(APPLICATION), default_timeout=20).run()

    def test_categories_principales_puis_toutes_les_categories(self):
        self.app.sidebar.radio[0].set_value("Catégories").run()
        self.assertFalse(self.app.exception)
        graphique = json.loads(self.app.get("plotly_chart")[0].proto.spec)
        self.assertEqual(len(graphique["data"][0]["y"]), 10)

        self.app.checkbox[0].set_value(True).run()
        graphique = json.loads(self.app.get("plotly_chart")[0].proto.spec)
        self.assertEqual(len(graphique["data"][0]["y"]), 24)

    def test_navigation_et_filtres_de_paiement(self):
        for page in ["Vue d’ensemble", "Catégories", "Paiements", "Clients", "Explorer les données", "Comprendre et présenter"]:
            self.app.sidebar.radio[0].set_value(page).run()
            self.assertFalse(self.app.exception, page)

        self.app.sidebar.radio[0].set_value("Explorer les données").run()
        choix = next(radio for radio in self.app.radio if radio.label == "Jeu de données")
        choix.set_value("Paiements").run()
        self.app.multiselect[0].set_value(["PAID"]).run()
        self.assertTrue(any("150 ligne(s)" in texte.value for texte in self.app.caption))


if __name__ == "__main__":
    unittest.main()
