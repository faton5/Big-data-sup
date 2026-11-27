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


# Les noms d'origine restent dans les données ; ces libellés facilitent la lecture.
CATEGORIES_FR = {
    "vehicle": "Véhicules", "motorcycle": "Motos", "mens-watches": "Montres homme",
    "womens-watches": "Montres femme", "laptops": "Ordinateurs portables", "furniture": "Meubles",
    "smartphones": "Smartphones", "mobile-accessories": "Accessoires mobiles", "tablets": "Tablettes",
    "mens-shoes": "Chaussures homme", "womens-bags": "Sacs femme", "kitchen-accessories": "Accessoires de cuisine",
    "fragrances": "Parfums", "womens-dresses": "Robes", "sports-accessories": "Accessoires de sport",
    "home-decoration": "Décoration", "tops": "Hauts", "groceries": "Épicerie", "womens-shoes": "Chaussures femme",
    "sunglasses": "Lunettes de soleil", "mens-shirts": "Chemises homme", "womens-jewellery": "Bijoux femme",
    "beauty": "Beauté", "skin-care": "Soins de la peau",
}

commandes, paiements = charger_donnees()
payes = paiements[paiements["payment_status"] == "PAID"].copy()
payes["mois"] = pd.to_datetime(payes["payment_date"]).dt.to_period("M").astype(str)
ca_commande = commandes["discounted_line_total"].sum()
encaisse = payes["amount"].sum()
nombre_paniers = len(paiements)
taux_accepte = len(payes) / nombre_paniers * 100 if nombre_paniers else 0
categories = commandes.groupby("category", as_index=False)["discounted_line_total"].sum().sort_values("discounted_line_total", ascending=False)
categories["libelle"] = categories["category"].map(CATEGORIES_FR).fillna(categories["category"])
mensuel = payes.groupby("mois", as_index=False)["amount"].sum().sort_values("mois")
clients = payes.groupby("user_id_pseudo", as_index=False)["amount"].sum().sort_values("amount", ascending=False).head(10).copy()
clients["pseudonyme"] = clients["user_id_pseudo"].str[:12]
if clients["pseudonyme"].nunique() != len(clients):
    clients["pseudonyme"] = clients["user_id_pseudo"]
statuts = paiements["payment_status"].value_counts().rename_axis("statut").reset_index(name="nombre")
statuts["libelle"] = statuts["statut"].map({"PAID": "Acceptés", "REFUSED": "Refusés", "PENDING": "En attente"})

st.markdown("""
<style>
.block-container { max-width: 1480px; padding-top: 2.25rem; padding-bottom: 4rem; }
[data-testid="stMetric"] {
    min-height: 124px; padding: 1.1rem 1.2rem; border: 1px solid rgba(126, 144, 177, .24);
    border-radius: 16px; background: rgba(116, 139, 208, .07);
}
[data-testid="stMetricValue"] { font-weight: 700; letter-spacing: -.035em; }
[data-testid="stSidebar"] [role="radiogroup"] { gap: .25rem; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    border-radius: 10px; padding: .55rem .7rem; transition: background .15s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(100, 125, 220, .09); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: rgba(100, 125, 220, .17); }
.brand { display: flex; align-items: center; gap: .75rem; margin: .25rem 0 1.5rem; }
.brand-mark {
    display: grid; place-items: center; flex: 0 0 40px; height: 40px; border-radius: 12px;
    background: #526bd7; color: #fff; font-size: 1.25rem; font-weight: 800;
}
.brand-name { font-size: 1.05rem; font-weight: 750; letter-spacing: -.03em; line-height: 1.2; }
.brand-subtitle { font-size: .78rem; opacity: .7; letter-spacing: .06em; }
.sidebar-note { margin-top: 1rem; padding: 1rem; border: 1px solid rgba(126, 144, 177, .22);
    border-radius: 14px; background: rgba(116, 139, 208, .08); line-height: 1.5; }
.sidebar-note p { margin: .35rem 0 0; font-size: .9rem; opacity: .8; }
.hero {
    display: flex; justify-content: space-between; gap: 2rem; align-items: center;
    padding: clamp(1.5rem, 3vw, 2.5rem); margin-bottom: .4rem; border-radius: 20px;
    background: linear-gradient(120deg, #192c50 0%, #2b4675 100%); color: #f7f9ff;
}
.hero-copy { max-width: 720px; }
.hero-kicker { color: #c5d3ff; font-size: .78rem; font-weight: 750; letter-spacing: .11em; text-transform: uppercase; }
.hero h1 { margin: .65rem 0 .75rem; padding: 0; color: #fff !important;
    font-size: clamp(2rem, 3.5vw, 3.1rem); font-weight: 750; letter-spacing: -.045em; line-height: 1.08; }
.hero h1 span { color: #bfd0ff; }
.hero p { margin: 0; color: #dce6fa; font-size: 1rem; line-height: 1.6; }
.hero-aside { min-width: 180px; padding-left: 1.5rem; border-left: 1px solid rgba(255, 255, 255, .24); }
.hero-aside strong { display: block; margin-bottom: .5rem; color: #fff; font-size: .9rem; }
.hero-aside span { display: block; color: #dce6fa; font-size: .9rem; line-height: 1.7; }
.section-label { margin: 1.1rem 0 .1rem; font-size: .8rem; font-weight: 750; letter-spacing: .08em; text-transform: uppercase; opacity: .75; }
@media (max-width: 700px) {
    .block-container { padding-top: 1.25rem; }
    .hero { display: block; }
    .hero-aside { display: none; }
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
<div class="brand">
  <div class="brand-mark" aria-hidden="true">C.</div>
  <div><div class="brand-name">Commerce</div><div class="brand-subtitle">ANALYTICS</div></div>
</div>
""", unsafe_allow_html=True)
    st.caption("EXPLORER LE PROJET")
    page = st.radio("Navigation", [
        "Vue d’ensemble", "Catégories", "Paiements", "Clients", "Explorer les données", "Comprendre et présenter"
    ], label_visibility="collapsed")
    st.divider()
    st.markdown("""
<div class="sidebar-note"><strong>Projet fil rouge · B2</strong>
<p>De la collecte à la présentation des résultats.</p></div>
""", unsafe_allow_html=True)
    st.caption("Données simulées et pseudonymisées")


def graphique_categories(donnees):
    figure = px.bar(donnees.sort_values("discounted_line_total"), x="discounted_line_total", y="libelle", orientation="h",
                    labels={"discounted_line_total": "Montant commandé", "libelle": "Catégorie"}, color_discrete_sequence=["#647be0"])
    figure.update_traces(hovertemplate="<b>%{y}</b><br>Montant commandé : %{x:,.2f}<extra></extra>")
    figure.update_layout(height=max(360, len(donnees) * 29), margin=dict(l=5, r=20, t=10, b=15),
                         showlegend=False, bargap=.3, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    figure.update_xaxes(showgrid=True, gridcolor="rgba(133,148,175,.15)", zeroline=False)
    figure.update_yaxes(showgrid=False, title_text=None, automargin=True)
    st.plotly_chart(figure, width="stretch")


def graphique_mensuel():
    figure = px.line(mensuel, x="mois", y="amount", markers=True,
                     labels={"mois": "Mois du paiement", "amount": "Montant encaissé"}, color_discrete_sequence=["#7087ed"])
    figure.update_traces(line_width=3, marker_size=8, fill="tozeroy", fillcolor="rgba(112,135,237,.10)",
                         hovertemplate="<b>%{x}</b><br>Montant encaissé : %{y:,.2f}<extra></extra>")
    figure.update_layout(height=330, margin=dict(l=5, r=15, t=15, b=10),
                         plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    figure.update_xaxes(showgrid=False, title_text="Mois du paiement")
    figure.update_yaxes(showgrid=True, gridcolor="rgba(133,148,175,.15)", zeroline=False, title_text="Montant encaissé")
    st.plotly_chart(figure, width="stretch")


def graphique_clients():
    figure = px.bar(clients.sort_values("amount"), x="amount", y="pseudonyme", orientation="h",
                    labels={"amount": "Montant encaissé", "pseudonyme": "Pseudonyme client (extrait)"}, color_discrete_sequence=["#8e7bd8"])
    figure.update_traces(hovertemplate="<b>%{y}</b><br>Montant encaissé : %{x:,.2f}<extra></extra>")
    figure.update_layout(height=420, margin=dict(l=5, r=20, t=10, b=15), bargap=.3,
                         plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    figure.update_xaxes(showgrid=True, gridcolor="rgba(133,148,175,.15)", zeroline=False)
    figure.update_yaxes(showgrid=False, automargin=True)
    st.plotly_chart(figure, width="stretch")


if page == "Vue d’ensemble":
    st.markdown("""
<div class="hero">
  <div class="hero-copy">
    <div class="hero-kicker">Commerce Analytics · Projet fil rouge</div>
    <h1>Les chiffres ont<br><span>quelque chose à dire.</span></h1>
    <p>Des données de commerce aux indicateurs essentiels : une lecture claire pour comprendre et présenter le projet.</p>
  </div>
  <div class="hero-aside"><strong>Le parcours du projet</strong><span>Collecter les données</span><span>Analyser les résultats</span><span>Présenter les découvertes</span></div>
</div>
""", unsafe_allow_html=True)
    st.markdown('<p class="section-label">Les indicateurs essentiels</p>', unsafe_allow_html=True)
    indicateurs = st.columns(4)
    indicateurs[0].metric("Montant commandé", montant(ca_commande), help="Somme des lignes de commande après réduction.")
    indicateurs[1].metric("Montant encaissé", montant(encaisse), help="Somme des paiements acceptés uniquement.")
    indicateurs[2].metric("Paniers analysés", f"{nombre_paniers}", help="Un paiement par panier a été vérifié dans le notebook.")
    indicateurs[3].metric("Paiements acceptés", f"{taux_accepte:.2f} %".replace(".", ","), help="Paiements PAID divisés par tous les paiements analysés.")
    st.caption("Montants exprimés dans l’unité du jeu de données, qui ne précise pas de devise.")
    gauche, droite = st.columns([1.6, 1], gap="medium")
    with gauche:
        with st.container(border=True):
            st.caption("DANS LE TEMPS")
            st.subheader("Les encaissements par mois")
            st.write("Les paiements acceptés, regroupés selon leur date.")
            graphique_mensuel()
            st.caption("Les dates sont simulées : cette courbe n’est pas un historique réel.")
    with droite:
        with st.container(border=True):
            st.caption("À RETENIR")
            st.subheader("La lecture en 3 idées")
            st.markdown("**Commandé**  ")
            st.write("La valeur des produits dans tous les paniers analysés.")
            st.markdown("**Encaissé**  ")
            st.write("La somme des paiements acceptés uniquement.")
            if not categories.empty:
                premiere = categories.iloc[0]
                st.markdown("**Catégorie en tête**  ")
                st.write(f"{premiere['libelle']} : {montant(premiere['discounted_line_total'])} commandés.")
            st.caption("Le menu permet d’approfondir chaque résultat.")

elif page == "Catégories":
    st.caption("ANALYSE DES COMMANDES")
    st.title("Que commandent les clients ?")
    st.write("Une lecture des catégories de produits, du montant le plus élevé au plus faible.")
    if not categories.empty:
        premiere = categories.iloc[0]
        part_premiere = premiere["discounted_line_total"] / ca_commande * 100 if ca_commande else 0
        indicateurs = st.columns(3)
        indicateurs[0].metric("Catégorie en tête", premiere["libelle"])
        indicateurs[1].metric("Part du montant commandé", f"{part_premiere:.1f} %".replace(".", ","))
        indicateurs[2].metric("Catégories analysées", str(len(categories)))
    with st.container(border=True):
        st.subheader("Montant commandé par catégorie")
        st.caption("Somme des lignes de produits après réduction, tous statuts de paiement confondus.")
        tout_afficher = st.checkbox("Afficher toutes les catégories", value=False)
        st.caption("Toutes les catégories" if tout_afficher else "Les 10 catégories les plus importantes")
        graphique_categories(categories if tout_afficher else categories.head(10))
        st.caption("Montant dans l’unité du jeu de données. Les libellés sont traduits pour la présentation.")
    st.info("À expliquer : on additionne `discounted_line_total`. Le total du panier est répété sur ses lignes, donc on ne l’additionne pas ici.")
    with st.expander("Voir le détail de toutes les catégories"):
        detail = categories[["libelle", "category", "discounted_line_total"]].rename(
            columns={"libelle": "Catégorie", "category": "Nom d’origine", "discounted_line_total": "Montant commandé"})
        st.dataframe(detail, hide_index=True, width="stretch")

elif page == "Paiements":
    st.caption("ANALYSE DES PAIEMENTS")
    st.title("Que s’est-il passé au paiement ?")
    st.write("Distinguer les paiements acceptés, refusés et en attente pour comprendre les encaissements.")
    colonnes = st.columns(3)
    for colonne, statut, titre in zip(colonnes, ["PAID", "REFUSED", "PENDING"], ["Acceptés", "Refusés", "En attente"]):
        colonne.metric(titre, str(int((paiements["payment_status"] == statut).sum())))
    gauche, droite = st.columns([1.45, 1], gap="medium")
    with gauche:
        with st.container(border=True):
            st.subheader("Encaissements par mois")
            st.caption("Somme des paiements acceptés selon leur date.")
            graphique_mensuel()
    with droite:
        with st.container(border=True):
            st.subheader("Les statuts de paiement")
            st.caption("Répartition des paiements analysés.")
            figure = px.pie(statuts, names="libelle", values="nombre", hole=0.62,
                            color="statut", color_discrete_map={"PAID": "#647be0", "REFUSED": "#c16c52", "PENDING": "#a17d32"})
            figure.update_traces(textposition="outside", textinfo="percent")
            figure.update_layout(height=330, margin=dict(l=10, r=10, t=15, b=10),
                                 legend_title_text=None, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(figure, width="stretch")
    st.warning("Les dates sont simulées. Pour chaque panier, le TP2 a retenu sa date la plus ancienne : cette courbe n’est pas un historique réel.")

elif page == "Clients":
    st.caption("ANALYSE DES CLIENTS")
    st.title("Qui contribue aux encaissements ?")
    st.write("Les dix clients pseudonymisés dont les paiements acceptés représentent les montants les plus élevés.")
    with st.container(border=True):
        st.subheader("Les 10 premiers clients")
        st.caption("Somme des paiements acceptés pour chaque pseudonyme.")
        graphique_clients()
        st.caption("Le graphique affiche les 12 premiers caractères du pseudonyme, sauf en cas de doublon. Le calcul utilise le pseudonyme complet.")
    st.info("À expliquer : un même client garde le même pseudonyme dans les deux jeux de données tant que la même clé est utilisée. Les données restent à protéger.")

elif page == "Explorer les données":
    st.caption("DONNÉES ANALYTIQUES")
    st.title("Explorer les données")
    st.write("Deux jeux de données pseudonymisés, avec uniquement les champs nécessaires aux analyses.")
    with st.container(border=True):
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
    st.caption("GUIDE DE PRÉSENTATION")
    st.title("À vous de raconter le projet.")
    st.write("Une étape à la fois : l’idée à expliquer, puis ce que vous pouvez montrer.")
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
    position = list(etapes).index(choix_etape) + 1
    st.progress(position / len(etapes), text=f"Étape {position} sur {len(etapes)}")
    idee, preuve = etapes[choix_etape]
    gauche, droite = st.columns(2, gap="medium")
    with gauche:
        with st.container(border=True):
            st.caption("À EXPLIQUER")
            st.subheader("L’idée principale")
            st.write(idee)
    with droite:
        with st.container(border=True):
            st.caption("À MONTRER")
            st.subheader("Pendant la démonstration")
            st.write(preuve)
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
