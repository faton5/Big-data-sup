from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


RACINE = Path(__file__).resolve().parent
st.set_page_config(page_title="Commerce Analytics | Jour 3", page_icon="📊", layout="wide")


def montant(valeur):
    return f"{valeur:,.2f}".replace(",", " ").replace(".", ",")


def charger_donnees():
    dossier = RACINE / "data"
    chemins = [dossier / "commandes_pseudonymisees.parquet", dossier / "paiements_pseudonymises.parquet"]
    if not all(chemin.exists() for chemin in chemins):
        st.error("Les fichiers Parquet sont absents. Exécute d’abord le notebook atelier_jour3.ipynb depuis le dossier jour-3.")
        st.stop()
    try:
        return pd.read_parquet(chemins[0]), pd.read_parquet(chemins[1])
    except (OSError, ValueError, ImportError) as erreur:
        st.error(f"Lecture des fichiers Parquet impossible : {erreur}")
        st.stop()


commandes, paiements = charger_donnees()
payes = paiements[paiements["payment_status"] == "PAID"].copy()
payes["mois"] = pd.to_datetime(payes["payment_date"]).dt.to_period("M").astype(str)
ca_commande = commandes["discounted_line_total"].sum()
encaisse = payes["amount"].sum()
nombre_paniers = len(paiements)
taux_accepte = len(payes) / nombre_paniers * 100 if nombre_paniers else 0
categories = commandes.groupby("category", as_index=False)["discounted_line_total"].sum().sort_values("discounted_line_total", ascending=False)
mensuel = payes.groupby("mois", as_index=False)["amount"].sum().sort_values("mois")
clients = payes.groupby("user_id_pseudo", as_index=False)["amount"].sum().sort_values("amount", ascending=False).head(10).copy()
clients["pseudonyme"] = clients["user_id_pseudo"].str[:12]
if clients["pseudonyme"].nunique() != len(clients):
    clients["pseudonyme"] = clients["user_id_pseudo"]
statuts = paiements["payment_status"].value_counts().rename_axis("statut").reset_index(name="nombre")

st.markdown("""
<style>
[data-testid="stMetric"] { border: 1px solid rgba(128, 128, 128, 0.3); border-radius: 14px; padding: 18px; }
.block-container { padding-top: 2rem; padding-bottom: 4rem; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.caption("PROJET FIL ROUGE · B2")
    st.title("Commerce Analytics")
    st.write("Des données aux décisions, en trois journées.")
    page = st.radio("Navigation", [
        "Vue d’ensemble", "Catégories", "Paiements", "Clients", "Explorer les données", "Comprendre et présenter"
    ])
    st.divider()
    st.caption("Jour 3 · Fichiers pseudonymisés")
    st.caption("Données simulées : elles ne décrivent pas une activité réelle.")


def graphique_categories():
    figure = px.bar(categories.sort_values("discounted_line_total"), x="discounted_line_total", y="category", orientation="h",
                    labels={"discounted_line_total": "Montant commandé", "category": "Catégorie"}, color_discrete_sequence=["#287a78"])
    figure.update_layout(height=max(450, len(categories) * 25), margin=dict(l=10, r=20, t=20, b=20), showlegend=False)
    st.plotly_chart(figure, width="stretch")


def graphique_mensuel():
    figure = px.line(mensuel, x="mois", y="amount", markers=True,
                     labels={"mois": "Mois du paiement", "amount": "Montant encaissé"}, color_discrete_sequence=["#ce6c4c"])
    figure.update_layout(margin=dict(l=10, r=20, t=20, b=20))
    st.plotly_chart(figure, width="stretch")


def graphique_clients():
    figure = px.bar(clients.sort_values("amount"), x="amount", y="pseudonyme", orientation="h",
                    labels={"amount": "Montant encaissé", "pseudonyme": "Pseudonyme client (extrait)"}, color_discrete_sequence=["#6177aa"])
    figure.update_layout(height=440, margin=dict(l=10, r=20, t=20, b=20))
    st.plotly_chart(figure, width="stretch")


if page == "Vue d’ensemble":
    st.caption("TABLEAU DE BORD · JOUR 3")
    st.title("Les chiffres, en clair.")
    st.write("Comprendre les commandes, les paiements et les clients du projet en quelques étapes.")
    indicateurs = st.columns(4)
    indicateurs[0].metric("Montant commandé", montant(ca_commande), help="Somme des lignes de commande après réduction.")
    indicateurs[1].metric("Montant encaissé", montant(encaisse), help="Somme des paiements acceptés uniquement.")
    indicateurs[2].metric("Paniers analysés", f"{nombre_paniers}", help="Un paiement par panier a été vérifié dans le notebook.")
    indicateurs[3].metric("Paiements acceptés", f"{taux_accepte:.2f} %".replace(".", ","), help="Paiements PAID divisés par tous les paiements analysés.")
    st.caption("Les montants sont exprimés dans l’unité du jeu de données, qui ne précise pas de devise.")
    st.divider()
    gauche, droite = st.columns([1.2, 1])
    with gauche:
        st.subheader("Les encaissements dans le temps")
        st.write("Seuls les paiements acceptés sont additionnés, selon leur date de paiement.")
        graphique_mensuel()
    with droite:
        st.subheader("Comment lire ces chiffres ?")
        st.markdown("""
- **Commandé** : ce que contiennent les paniers, même si le paiement n’a pas abouti.
- **Encaissé** : ce qui correspond aux paiements acceptés (`PAID`).
- **Acceptation** : part des paiements acceptés parmi tous les paiements analysés.
- Les dates et les montants sont issus d’un jeu simulé.
        """)
        if not categories.empty:
            premier = categories.iloc[0]
            st.info(f"La catégorie qui pèse le plus dans les commandes est **{premier['category']}**, avec **{montant(premier['discounted_line_total'])}**.")
        st.write("Utilise le menu pour explorer chaque sujet ou préparer la présentation.")

elif page == "Catégories":
    st.caption("ANALYSE 01")
    st.title("Que commandent les clients ?")
    st.write("Montant commandé par catégorie, calculé à partir des lignes de produits après réduction.")
    graphique_categories()
    st.info("On additionne `discounted_line_total`. On ne répète pas le total du panier pour chaque ligne de produit.")
    with st.expander("Voir le détail des catégories"):
        st.dataframe(categories.rename(columns={"category": "Catégorie", "discounted_line_total": "Montant commandé"}), hide_index=True, width="stretch")

elif page == "Paiements":
    st.caption("ANALYSE 02")
    st.title("Que s’est-il passé au paiement ?")
    st.write("On distingue les tentatives acceptées, refusées et en attente avant d’étudier les montants encaissés.")
    colonnes = st.columns(3)
    for colonne, statut, titre in zip(colonnes, ["PAID", "REFUSED", "PENDING"], ["Acceptés", "Refusés", "En attente"]):
        colonne.metric(titre, str(int((paiements["payment_status"] == statut).sum())))
    gauche, droite = st.columns([1.2, 1])
    with gauche:
        st.subheader("Encaissements par mois")
        graphique_mensuel()
    with droite:
        st.subheader("Répartition des statuts")
        figure = px.pie(statuts, names="statut", values="nombre", hole=0.55,
                        color="statut", color_discrete_map={"PAID": "#287a78", "REFUSED": "#d67e65", "PENDING": "#e6b85b"})
        figure.update_layout(margin=dict(l=10, r=10, t=20, b=20))
        st.plotly_chart(figure, width="stretch")
    st.warning("Les dates sont simulées. Pour chaque panier, le TP2 a retenu sa date la plus ancienne : cette courbe n’est pas un historique réel.")

elif page == "Clients":
    st.caption("ANALYSE 03")
    st.title("Qui contribue aux encaissements ?")
    st.write("Les dix clients pseudonymisés dont les paiements acceptés représentent les montants les plus élevés.")
    graphique_clients()
    st.caption("Pour la lisibilité, le graphique affiche les 12 premiers caractères du pseudonyme, sauf en cas de doublon. Le calcul utilise le pseudonyme complet.")
    st.info("Un même client garde le même pseudonyme dans les commandes et les paiements tant que la même clé est utilisée. Les données restent à protéger.")

elif page == "Explorer les données":
    st.caption("DONNÉES ANALYTIQUES")
    st.title("Explorer les données")
    st.write("Ces tableaux proviennent des deux fichiers Parquet et contiennent seulement les champs nécessaires aux analyses.")
    choix = st.radio("Jeu de données", ["Commandes", "Paiements"], horizontal=True)
    tableau = commandes.copy() if choix == "Commandes" else paiements.copy()
    recherche = st.text_input("Rechercher un pseudonyme", placeholder="Saisir tout ou partie du pseudonyme")
    if recherche:
        tableau = tableau[tableau["user_id_pseudo"].str.contains(recherche.strip(), case=False, regex=False, na=False)]
    if choix == "Paiements":
        selection = st.multiselect("Statuts", ["PAID", "REFUSED", "PENDING"], default=["PAID", "REFUSED", "PENDING"])
        tableau = tableau[tableau["payment_status"].isin(selection)]
    else:
        selection = st.multiselect("Catégories", sorted(commandes["category"].unique()))
        if selection:
            tableau = tableau[tableau["category"].isin(selection)]
    st.caption(f"{len(tableau)} ligne(s) affichée(s)")
    st.dataframe(tableau, hide_index=True, width="stretch")

else:
    st.caption("PRÉPARATION À L’ORAL")
    st.title("Comprendre et présenter le projet")
    st.write("Suis le fil : une étape à la fois, avec une idée à expliquer et une preuve à montrer.")
    etapes = {
        "1 · Présenter le besoin": (
            "Transformer des données de commerce simulées en indicateurs simples pour comprendre les commandes et les paiements.",
            "Montrer la vue d’ensemble et expliquer la différence entre montant commandé et montant encaissé."),
        "2 · Collecter et stocker": (
            "Au jour 1, les données ont été collectées depuis DummyJSON et préparées en CSV. Au jour 2, Python les a chargées dans les collections MongoDB.",
            "Montrer les collections et expliquer que MongoDB conserve les données sources."),
        "3 · Calculer les indicateurs": (
            "PySpark a traité les données du jour 2 : montants par catégorie, paiements par mois, taux de refus et principaux clients.",
            "Montrer les résultats du TP2 ; expliquer que les paiements refusés ne sont pas encaissés."),
        "4 · Protéger les identifiants": (
            "Le jour 3, HMAC-SHA-256 utilise une clé secrète pour remplacer chaque identifiant par un pseudonyme stable dans les deux sources.",
            "Montrer le notebook, puis expliquer que la clé reste privée et que pseudonymiser ne veut pas dire anonymiser."),
        "5 · Préparer les données": (
            "Pandas convertit les montants et dates, écarte les valeurs invalides et exporte seulement les colonnes utiles en deux fichiers Parquet.",
            "Montrer les fichiers de commandes et de paiements : ils ne contiennent ni identifiant direct ni clé."),
        "6 · Interpréter les graphiques": (
            "Comparer les catégories, suivre les paiements acceptés par mois et observer le Top 10 des clients pseudonymisés.",
            "Montrer les trois graphiques Matplotlib et les vues interactives. Rappeler que les dates sont simulées."),
        "7 · Conclure et discuter des limites": (
            "La chaîne relie collecte, stockage, calcul, sécurité et visualisation. Les données fictives permettent de comprendre la méthode.",
            "Rappeler que les pseudonymes restent des données à protéger et que les montants ne représentent pas une activité réelle."),
    }
    choix_etape = st.selectbox("Étape de la présentation", list(etapes))
    idee, preuve = etapes[choix_etape]
    st.subheader("L’idée à expliquer")
    st.write(idee)
    st.subheader("Ce qu’on peut montrer")
    st.write(preuve)
    st.divider()
    st.subheader("Questions possibles")
    with st.expander("Pourquoi le montant commandé diffère-t-il du montant encaissé ?"):
        st.write("Les commandes incluent tous les paniers analysés ; les encaissements ne retiennent que les paiements au statut PAID.")
    with st.expander("Pourquoi ne pas afficher les identifiants clients ?"):
        st.write("Le pseudonyme limite leur exposition tout en permettant de regrouper les paiements d’un même client. Il ne rend pas les données anonymes.")
    with st.expander("Pourquoi utiliser Parquet ?"):
        st.write("Ce format en colonnes conserve les types et convient aux traitements analytiques. Ici, il permet au dashboard de lire les données préparées sans accéder à MongoDB.")
    with st.expander("Quelle est la limite de l’évolution mensuelle ?"):
        st.write("Les dates sont simulées et la date de paiement est calculée à partir de la date la plus ancienne du panier. La courbe illustre le traitement, pas des ventes réelles.")
    st.code("""API / CSV → Python → MongoDB
                     ├→ PySpark → indicateurs du TP2 → comparaison
                     └→ Pandas + HMAC → Parquet → Matplotlib / Streamlit""", language=None)
