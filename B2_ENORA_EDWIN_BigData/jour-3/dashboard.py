"""Petit serveur local pour consulter les données du projet Big Data."""

import argparse
import json
import math
import re
from datetime import date, datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError


DOSSIER_SITE = Path(__file__).resolve().parent / "site"
URI_MONGO = "mongodb://127.0.0.1:27017"
COLLECTIONS = {
    "raw_commandes": "Commandes",
    "raw_payments": "Paiements",
    "raw_products": "Produits",
    "raw_carts": "Paniers",
    "raw_users": "Clients",
    "raw_posts": "Publications",
    "raw_comments": "Commentaires",
    "raw_recipes": "Recettes",
    "raw_quotes": "Citations",
    "raw_todos": "Tâches",
}
CHAMPS_SENSIBLES = {
    "password", "token", "ssn", "ein", "ip", "macaddress", "cardnumber", "cardexpire", "iban", "wallet",
    "email", "phone", "birthdate", "bloodgroup", "address", "postalcode", "coordinates",
}


def nettoyer_document(valeur):
    """Rend un document lisible en masquant quelques champs sensibles."""
    if isinstance(valeur, dict):
        resultat = {}
        for cle, contenu in valeur.items():
            if cle.lower() == "address" and isinstance(contenu, dict):
                resultat[cle] = nettoyer_document(contenu)
            elif cle.lower() in CHAMPS_SENSIBLES:
                resultat[cle] = "[masqué]"
            else:
                resultat[cle] = nettoyer_document(contenu)
        return resultat
    if isinstance(valeur, list):
        return [nettoyer_document(element) for element in valeur]
    if isinstance(valeur, (ObjectId, date, datetime)):
        return str(valeur)
    if valeur is None or isinstance(valeur, (str, int, float, bool)):
        return valeur
    return str(valeur)


def analyser(commandes, paiements):
    """Calcule les indicateurs à partir des lignes et des paiements MongoDB."""
    statuts = {
        "PAID": {"statut": "PAID", "nombre": 0, "montant": 0.0},
        "REFUSED": {"statut": "REFUSED", "nombre": 0, "montant": 0.0},
        "PENDING": {"statut": "PENDING", "nombre": 0, "montant": 0.0},
    }
    paniers_payes = set()
    clients = {}
    mois = {}
    paniers_paiements = []

    for paiement in paiements:
        statut = paiement.get("statut", "INCONNU")
        montant = float(paiement.get("montant") or 0)
        panier = paiement.get("cart_id")
        if panier is not None:
            paniers_paiements.append(panier)
        if statut not in statuts:
            statuts[statut] = {"statut": statut, "nombre": 0, "montant": 0.0}
        statuts[statut]["nombre"] += 1
        statuts[statut]["montant"] += montant

        if statut == "PAID":
            paniers_payes.add(panier)
            client = paiement.get("user_id")
            clients[client] = clients.get(client, 0.0) + montant
            date_paiement = str(paiement.get("date_paiement") or "")
            if len(date_paiement) >= 7:
                periode = date_paiement[:7]
                mois[periode] = mois.get(periode, 0.0) + montant

    categories = {}
    paniers = set()
    dates_par_panier = {}
    for ligne in commandes:
        panier = ligne.get("cart_id")
        if panier is not None:
            paniers.add(panier)
            date_commande = ligne.get("order_date")
            if date_commande:
                dates_par_panier.setdefault(panier, set()).add(str(date_commande))
        categorie = ligne.get("category") or "Sans catégorie"
        montant = float(ligne.get("discounted_line_total") or 0)
        if categorie not in categories:
            categories[categorie] = {"nom": categorie, "commande": 0.0, "encaisse": 0.0}
        categories[categorie]["commande"] += montant
        if panier in paniers_payes:
            categories[categorie]["encaisse"] += montant

    for valeur in statuts.values():
        valeur["montant"] = round(valeur["montant"], 2)
    for valeur in categories.values():
        valeur["commande"] = round(valeur["commande"], 2)
        valeur["encaisse"] = round(valeur["encaisse"], 2)

    total = len(paiements)
    refuses = statuts["REFUSED"]["nombre"]
    liste_clients = [{"user_id": identifiant, "montant": round(montant, 2)} for identifiant, montant in clients.items()]
    def cle_client(client):
        identifiant = client["user_id"]
        if isinstance(identifiant, int):
            return (-client["montant"], 0, identifiant)
        return (-client["montant"], 1, str(identifiant))

    liste_clients.sort(key=cle_client)
    liste_categories = sorted(categories.values(), key=lambda item: (-item["commande"], item["nom"]))

    return {
        "lignes_commandes": len(commandes),
        "paniers": len(paniers),
        "paiements": total,
        "encaisse": statuts["PAID"]["montant"],
        "commande": round(sum(item["commande"] for item in liste_categories), 2),
        "taux_refus": round(refuses * 100 / total, 2) if total else 0,
        "statuts": list(statuts.values()),
        "categories": liste_categories,
        "top_clients": liste_clients[:10],
        "mensuel": [{"mois": periode, "montant": round(mois[periode], 2)} for periode in sorted(mois)],
        "paniers_dates_multiples": sum(len(dates) > 1 for dates in dates_par_panier.values()),
        "doublons_paiements": len(paniers_paiements) - len(set(paniers_paiements)),
    }


def construire_recherche(texte):
    if not texte:
        return {}
    texte = texte[:100]
    motif = re.escape(texte)
    champs = [
        "title", "name", "body", "quote", "author", "todo", "category", "brand", "cuisine", "difficulty",
        "product_title", "order_id", "payment_id", "statut", "date_paiement", "order_date", "firstName", "lastName", "username",
    ]
    conditions = [{champ: {"$regex": motif, "$options": "i"}} for champ in champs]
    if texte.isdigit():
        numero = int(texte)
        champs_numeriques = ["id", "cart_id", "user_id", "numero_ligne", "userId", "postId", "product_id", "quantity", "stock", "totalProducts", "totalQuantity", "age", "views", "likes", "servings"]
        conditions.extend({champ: numero} for champ in champs_numeriques)
    try:
        montant_recherche = float(texte.replace(",", "."))
        if math.isfinite(montant_recherche):
            conditions.extend({champ: montant_recherche} for champ in ["price", "montant", "discountedTotal", "discounted_line_total"])
    except ValueError:
        pass
    if texte.lower() in {"oui", "vrai", "true"}:
        conditions.append({"completed": True})
    elif texte.lower() in {"non", "faux", "false"}:
        conditions.append({"completed": False})
    return {"$or": conditions}


class Gestionnaire(SimpleHTTPRequestHandler):
    client_mongo = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DOSSIER_SITE), **kwargs)

    def envoyer_json(self, donnees, statut=200):
        contenu = json.dumps(nettoyer_document(donnees), ensure_ascii=False).encode("utf-8")
        self.send_response(statut)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(contenu)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(contenu)

    def do_GET(self):
        url = urlparse(self.path)
        if not url.path.startswith("/api/"):
            return super().do_GET()

        try:
            self.client_mongo.admin.command("ping")
            base = self.client_mongo["commerce"]
            if url.path == "/api/vue-ensemble":
                commandes = list(base.raw_commandes.find({}, {"_id": 0, "cart_id": 1, "category": 1, "discounted_line_total": 1, "order_date": 1}))
                paiements = list(base.raw_payments.find({}, {"_id": 0, "cart_id": 1, "user_id": 1, "montant": 1, "statut": 1, "date_paiement": 1}))
                resultats = analyser(commandes, paiements)
                resultats["collections"] = [
                    {"nom": nom, "libelle": libelle, "nombre": base[nom].count_documents({})}
                    for nom, libelle in COLLECTIONS.items()
                ]
                resultats["actualise_le"] = datetime.now(timezone.utc).isoformat()
                return self.envoyer_json(resultats)

            if url.path.startswith("/api/collection/"):
                nom = url.path.removeprefix("/api/collection/")
                if nom not in COLLECTIONS:
                    return self.envoyer_json({"erreur": "Collection introuvable."}, 404)
                parametres = parse_qs(url.query)
                try:
                    page = max(1, int(parametres.get("page", ["1"])[0]))
                except ValueError:
                    return self.envoyer_json({"erreur": "Numéro de page invalide."}, 400)
                recherche = parametres.get("q", [""])[0].strip()
                filtre = construire_recherche(recherche)
                par_page = 10
                collection = base[nom]
                nombre = collection.count_documents(filtre)
                documents = list(collection.find(filtre).sort("_id", 1).skip((page - 1) * par_page).limit(par_page))
                return self.envoyer_json({
                    "collection": nom,
                    "libelle": COLLECTIONS[nom],
                    "total": nombre,
                    "page": page,
                    "par_page": par_page,
                    "documents": documents,
                })
            return self.envoyer_json({"erreur": "Adresse introuvable."}, 404)
        except PyMongoError:
            return self.envoyer_json({"erreur": "MongoDB ne répond pas. Démarre le conteneur avec : docker start mongo"}, 503)


def main():
    arguments = argparse.ArgumentParser(description="Tableau de bord BigData Commerce Analytics")
    arguments.add_argument("--port", type=int, default=8050, help="port local du site (8050 par défaut)")
    options = arguments.parse_args()
    serveur = ThreadingHTTPServer(("127.0.0.1", options.port), Gestionnaire)
    Gestionnaire.client_mongo = MongoClient(URI_MONGO, serverSelectionTimeoutMS=2500)
    print(f"Site disponible sur http://127.0.0.1:{options.port}", flush=True)
    print("Appuie sur Ctrl+C pour arrêter le site.", flush=True)
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        serveur.server_close()
        Gestionnaire.client_mongo.close()


if __name__ == "__main__":
    main()
