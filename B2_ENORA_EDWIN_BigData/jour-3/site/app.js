const $ = (selector) => document.querySelector(selector);
const nombre = new Intl.NumberFormat("fr-FR");
const montant = new Intl.NumberFormat("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const compact = new Intl.NumberFormat("fr-FR", { notation: "compact", maximumFractionDigits: 1 });

const libellesCategories = {
  vehicle: "Véhicules", motorcycle: "Motos", "mens-watches": "Montres homme", "womens-watches": "Montres femme",
  laptops: "Ordinateurs", furniture: "Mobilier", smartphones: "Smartphones", "mobile-accessories": "Accessoires mobiles",
  tablets: "Tablettes", "mens-shoes": "Chaussures homme", "womens-shoes": "Chaussures femme", "womens-bags": "Sacs",
  "kitchen-accessories": "Cuisine", fragrances: "Parfums", "womens-dresses": "Robes", "sports-accessories": "Sport",
  "home-decoration": "Décoration", tops: "Hauts", groceries: "Épicerie", sunglasses: "Lunettes de soleil",
  "mens-shirts": "Chemises homme", "womens-jewellery": "Bijoux", beauty: "Beauté", "skin-care": "Soins",
};

const colonnes = {
  raw_commandes: [["numero_ligne", "Ligne"], ["cart_id", "Panier"], ["product_title", "Produit"], ["category", "Catégorie"], ["quantity", "Quantité"], ["discounted_line_total", "Montant"]],
  raw_payments: [["payment_id", "Paiement"], ["cart_id", "Panier"], ["user_id", "Client"], ["montant", "Montant"], ["statut", "Statut"], ["date_paiement", "Date"]],
  raw_products: [["id", "ID"], ["title", "Produit"], ["category", "Catégorie"], ["price", "Prix"], ["stock", "Stock"]],
  raw_carts: [["id", "Panier"], ["userId", "Client"], ["totalProducts", "Produits"], ["totalQuantity", "Quantité"], ["discountedTotal", "Montant"]],
  raw_users: [["id", "ID"], ["firstName", "Prénom"], ["lastName", "Nom"], ["age", "Âge"], ["username", "Identifiant"]],
  raw_posts: [["id", "ID"], ["title", "Titre"], ["userId", "Client"], ["views", "Vues"]],
  raw_comments: [["id", "ID"], ["body", "Commentaire"], ["postId", "Publication"], ["likes", "Mentions"]],
  raw_recipes: [["id", "ID"], ["name", "Recette"], ["cuisine", "Cuisine"], ["difficulty", "Difficulté"], ["servings", "Portions"]],
  raw_quotes: [["id", "ID"], ["quote", "Citation"], ["author", "Auteur"]],
  raw_todos: [["id", "ID"], ["todo", "Tâche"], ["completed", "Terminée"], ["userId", "Client"]],
};

const etat = { donnees: null, metrique: "commande", toutesCategories: false, page: 1, recherche: "", documents: [], derniereRequete: 0, etapeGuide: 0, signatureGuide: "" };

function proteger(texte) {
  return String(texte ?? "").replace(/[&<>"']/g, (caractere) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[caractere]));
}

function categorieLisible(categorie) {
  return libellesCategories[categorie] || String(categorie || "Sans catégorie").replaceAll("-", " ");
}

function statutInfo(statut) {
  const infos = {
    PAID: { label: "Acceptés", couleur: "#5e79df", classe: "paid", singulier: "Accepté" },
    REFUSED: { label: "Refusés", couleur: "#eea196", classe: "refused", singulier: "Refusé" },
    PENDING: { label: "En attente", couleur: "#f3cc83", classe: "pending", singulier: "En attente" },
  };
  return infos[statut] || { label: statut, couleur: "#acb7c8", classe: "pending", singulier: statut };
}

async function chargerJson(url) {
  const reponse = await fetch(url, { cache: "no-store" });
  const resultat = await reponse.json();
  if (!reponse.ok) throw new Error(resultat.erreur || "Impossible de charger les données.");
  return resultat;
}

function actualiserConnexion(enLigne, message = "") {
  const statut = $("#connection-status");
  statut.classList.toggle("offline", !enLigne);
  statut.lastElementChild.textContent = enLigne ? "MongoDB connecté" : "MongoDB indisponible";
  $("#error-box").hidden = enLigne;
  if (!enLigne) $("#error-message").textContent = message || "Vérifie que le conteneur est démarré.";
}

function afficherIndicateurs(data) {
  const payes = data.statuts.find((item) => item.statut === "PAID")?.nombre || 0;
  const refuses = data.statuts.find((item) => item.statut === "REFUSED")?.nombre || 0;
  const documents = data.collections.reduce((total, item) => total + item.nombre, 0);
  $("#stat-encaisse").textContent = montant.format(data.encaisse);
  $("#stat-paniers").textContent = nombre.format(data.paniers);
  $("#stat-refus").textContent = `${nombre.format(data.taux_refus)} %`;
  $("#stat-collections").textContent = nombre.format(data.collections.length);
  $("#stat-paid-caption").textContent = `${nombre.format(payes)} paiements acceptés`;
  $("#stat-lines-caption").textContent = `${nombre.format(data.lignes_commandes)} lignes de produits`;
  $("#stat-refused-caption").textContent = `${nombre.format(refuses)} paiements refusés sur ${nombre.format(data.paiements)}`;
  $("#stat-documents-caption").textContent = `${nombre.format(documents)} documents disponibles`;
  const heure = new Date(data.actualise_le).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
  $("#updated-at").textContent = `Actualisé à ${heure}`;
  $("#date-note").textContent = `${nombre.format(data.paniers_dates_multiples)} paniers ont plusieurs dates synthétiques. Le mois utilise la plus ancienne date retenue pour le paiement.`;
}

function afficherCategories() {
  if (!etat.donnees) return;
  const liste = [...etat.donnees.categories].sort((a, b) => b[etat.metrique] - a[etat.metrique] || a.nom.localeCompare(b.nom));
  const visibles = etat.toutesCategories ? liste : liste.slice(0, 6);
  const maximum = Math.max(...liste.map((item) => item[etat.metrique]), 1);
  $("#categories-description").textContent = etat.metrique === "commande"
    ? "Les montants des lignes de tous les paniers."
    : "Les montants des lignes des paniers payés.";
  $("#all-categories").textContent = etat.toutesCategories ? "Afficher moins" : "Voir toutes les catégories";
  $("#all-categories").hidden = liste.length <= 6;
  $("#category-chart").innerHTML = visibles.length ? visibles.map((item) => `
    <div class="category-row">
      <span class="category-name" title="${proteger(item.nom)}">${proteger(categorieLisible(item.nom))}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${Math.max(0, item[etat.metrique] / maximum * 100)}%"></div></div>
      <span class="category-value">${proteger(montant.format(item[etat.metrique]))}</span>
    </div>`).join("") : '<p class="placeholder">Aucune catégorie disponible.</p>';
}

function afficherPaiements(data) {
  $("#donut-total").textContent = nombre.format(data.paiements);
  let debut = 0;
  const portions = [];
  for (const item of data.statuts) {
    if (!item.nombre || !data.paiements) continue;
    const fin = debut + item.nombre / data.paiements * 100;
    portions.push(`${statutInfo(item.statut).couleur} ${debut}% ${fin}%`);
    debut = fin;
  }
  $("#payment-donut").style.background = portions.length ? `conic-gradient(${portions.join(",")})` : "#edf1f8";
  $("#payment-legend").innerHTML = data.statuts.map((item) => {
    const info = statutInfo(item.statut);
    const pourcentage = data.paiements ? item.nombre / data.paiements * 100 : 0;
    return `<div class="legend-row"><span class="legend-name"><span class="legend-dot" style="background:${info.couleur}"></span>${proteger(info.label)}</span><span class="legend-value">${nombre.format(item.nombre)}<small>${nombre.format(Math.round(pourcentage * 10) / 10)} %</small></span></div>`;
  }).join("");
}

function afficherEvolution(data) {
  if (!data.mensuel.length) {
    $("#monthly-chart").innerHTML = '<p class="placeholder">Aucun paiement accepté à afficher.</p>';
    return;
  }
  const largeur = 640, hauteur = 230, gauche = 52, droite = 20, haut = 20, bas = 42;
  const largeurUtile = largeur - gauche - droite, hauteurUtile = hauteur - haut - bas;
  const maximum = Math.max(...data.mensuel.map((item) => item.montant), 1);
  const points = data.mensuel.map((item, index) => ({
    x: gauche + (data.mensuel.length === 1 ? largeurUtile / 2 : index * largeurUtile / (data.mensuel.length - 1)),
    y: haut + hauteurUtile - item.montant / maximum * hauteurUtile,
    item,
  }));
  const ligne = points.map((point, index) => `${index ? "L" : "M"}${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(" ");
  const aire = `${ligne} L${points.at(-1).x.toFixed(1)},${haut + hauteurUtile} L${points[0].x.toFixed(1)},${haut + hauteurUtile} Z`;
  const grille = [0, 0.25, 0.5, 0.75, 1].map((part) => {
    const y = haut + hauteurUtile - part * hauteurUtile;
    return `<line class="gridline" x1="${gauche}" x2="${largeur - droite}" y1="${y}" y2="${y}"/><text class="axis-label" x="${gauche - 8}" y="${y + 4}" text-anchor="end">${proteger(compact.format(maximum * part))}</text>`;
  }).join("");
  const pointsSvg = points.map((point) => {
    const date = new Date(`${point.item.mois}-01T12:00:00`);
    const libelle = Number.isNaN(date.valueOf()) ? point.item.mois : date.toLocaleDateString("fr-FR", { month: "short" });
    return `<circle cx="${point.x}" cy="${point.y}" r="4" fill="#fff" stroke="#5d78df" stroke-width="2.5"><title>${proteger(point.item.mois)} : ${proteger(montant.format(point.item.montant))}</title></circle><text class="axis-label" x="${point.x}" y="${hauteur - 14}" text-anchor="middle">${proteger(libelle)}</text>`;
  }).join("");
  $("#monthly-chart").innerHTML = `<svg viewBox="0 0 ${largeur} ${hauteur}" role="img" aria-label="Évolution mensuelle des paiements acceptés"><defs><linearGradient id="area-gradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#7992ed" stop-opacity=".20"/><stop offset="100%" stop-color="#7992ed" stop-opacity="0"/></linearGradient></defs>${grille}<path d="${aire}" fill="url(#area-gradient)"/><path d="${ligne}" fill="none" stroke="#5d78df" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>${pointsSvg}</svg>`;
}

function afficherClients(data) {
  $("#client-list").innerHTML = data.top_clients.length ? data.top_clients.map((client, index) => `
    <div class="client-row"><span class="client-name"><span class="client-number">${String(index + 1).padStart(2, "0")}</span>Client #${proteger(client.user_id)}</span><strong class="client-amount">${proteger(montant.format(client.montant))}</strong></div>`).join("") : '<p class="placeholder">Aucun paiement accepté à afficher.</p>';
}

function preparerEtapes(data) {
  const total = data ? nombre.format(data.paiements) : "—";
  const lignes = data ? nombre.format(data.lignes_commandes) : "—";
  const paniers = data ? nombre.format(data.paniers) : "—";
  const statut = (nom) => data ? nombre.format(data.statuts.find((item) => item.statut === nom)?.nombre || 0) : "—";
  const encaisse = data ? montant.format(data.encaisse) : "—";
  const refus = data ? nombre.format(data.taux_refus) : "—";
  const datesMultiples = data ? nombre.format(data.paniers_dates_multiples) : "plusieurs";
  const premiereCategorie = data?.categories[0];
  const premierClient = data?.top_clients[0];
  const phraseCategorie = premiereCategorie
    ? `La catégorie ${categorieLisible(premiereCategorie.nom)} représente ${montant.format(premiereCategorie.commande)} de montant commandé.`
    : "Le graphique compare les montants des différentes catégories de produits.";
  const phraseClient = premierClient
    ? `Le client fictif #${premierClient.user_id} arrive en tête avec ${montant.format(premierClient.montant)} encaissés.`
    : "Le classement des clients utilise uniquement les paiements acceptés.";

  return [
    {
      titre: "Le projet en une phrase",
      description: "Notre objectif est de suivre des données de commerce depuis leur collecte jusqu’à leur présentation.",
      points: ["Récupérer des données de démonstration et des lignes de commandes.", "Les stocker dans MongoDB, puis les analyser avec PySpark.", "Présenter les résultats dans un tableau de bord pour mieux les comprendre."],
      phrase: "Nous avons transformé des données brutes en indicateurs pour comprendre les commandes et les paiements.",
      lien: "#comprendre", lienTexte: "Voir le parcours des données",
    },
    {
      titre: "Les données de départ",
      description: "Une ligne de commande correspond à un produit, et un panier peut contenir plusieurs produits.",
      points: [`Le fichier contient ${lignes} lignes de produits pour ${paniers} paniers distincts.`, "L’API DummyJSON fournit aussi des produits, clients, recettes et autres ressources.", "Dans MongoDB, ces données sont rangées dans dix collections, consultables dans l’explorateur."],
      phrase: `Nous avons ${lignes} lignes, mais ${paniers} paniers, car un panier peut contenir plusieurs produits.`,
      lien: "#exploration", lienTexte: "Explorer les collections",
    },
    {
      titre: "Le parcours des données",
      description: "Nous avançons par étapes pour savoir d’où viennent les chiffres et comment ils sont traités.",
      points: ["Python récupère les ressources de l’API et le fichier de commandes du jour 1.", "MongoDB conserve les données brutes et les paiements simulés.", "Le notebook PySpark prépare les analyses ; ce site lit MongoDB et recalcule les indicateurs en Python."],
      phrase: "Les données passent de l’API et du fichier CSV à MongoDB, puis elles sont analysées avant d’être affichées.",
      lien: "#comprendre", lienTexte: "Revoir les étapes du projet",
    },
    {
      titre: "La simulation des paiements",
      description: "Le notebook crée une tentative de paiement par panier, avec trois issues possibles.",
      points: [`Sur ${total} tentatives : ${statut("PAID")} acceptées, ${statut("REFUSED")} refusées et ${statut("PENDING")} en attente.`, "Le tirage vise 70 % de paiements acceptés, 20 % de refus et 10 % en attente ; les proportions obtenues peuvent varier.", "La graine 42 permet de retrouver le même tirage avec les mêmes données et le même ordre."],
      phrase: `Nous simulons un paiement par panier. Le taux de refus observé est de ${refus} %.`,
      lien: "#analyses", lienTexte: "Voir les statuts des paiements",
    },
    {
      titre: "Lire les indicateurs",
      description: "Les graphiques distinguent ce qui a été commandé de ce qui a réellement été encaissé dans la simulation.",
      points: [phraseCategorie, phraseClient, `Le montant encaissé est de ${encaisse} : seuls les paiements PAID sont additionnés.`],
      phrase: "Le montant commandé concerne tous les paniers. Le montant encaissé ne garde que les paniers dont le paiement est accepté.",
      lien: "#analyses", lienTexte: "Voir les graphiques",
    },
    {
      titre: "Le rôle de MongoDB et de Spark",
      description: "MongoDB sert à stocker les documents ; Spark permet de les traiter et de calculer des indicateurs.",
      points: ["Dans le notebook, select et filter préparent des transformations sur les DataFrames.", "Une action comme show ou count demande un résultat : Spark lance alors les calculs nécessaires.", "Spark UI montre les Jobs, Stages et Tasks pendant la session ; ce site ne surveille pas Spark en direct."],
      phrase: "MongoDB conserve les données. Dans le notebook, Spark attend une action avant d’exécuter le traitement : c’est la lazy evaluation.",
      lien: "#comprendre", lienTexte: "Voir le rôle de chaque étape",
    },
    {
      titre: "Les limites à préciser",
      description: "Les résultats servent à comprendre une démarche, avec des données de démonstration.",
      points: ["Les données DummyJSON et les paiements sont fictifs : il ne s’agit pas d’un chiffre d’affaires réel.", `${datesMultiples} paniers ont plusieurs dates synthétiques. Le notebook retient la plus ancienne pour dater le paiement.`, "Les données clients sont fictives et certaines informations sensibles sont masquées dans l’explorateur."],
      phrase: "L’évolution mensuelle est une simulation : les dates ne représentent pas un historique réel de paiements.",
      lien: "#analyses", lienTexte: "Revoir l’évolution mensuelle",
    },
  ];
}

function afficherGuide() {
  const etapes = preparerEtapes(etat.donnees);
  const index = Math.max(0, Math.min(etat.etapeGuide, etapes.length - 1));
  etat.etapeGuide = index;
  const etape = etapes[index];
  const signature = JSON.stringify([index, etape]);
  if (signature === etat.signatureGuide) return;
  etat.signatureGuide = signature;
  $("#guide-count").textContent = `ÉTAPE ${index + 1} / ${etapes.length}`;
  $("#guide-title").textContent = etape.titre;
  $("#guide-description").textContent = etape.description;
  $("#guide-points").innerHTML = etape.points.map((point) => `<li>${proteger(point)}</li>`).join("");
  $("#guide-sentence").textContent = etape.phrase;
  $("#guide-link").href = etape.lien;
  $("#guide-link").textContent = etape.lienTexte;
  $("#guide-prev").disabled = index === 0;
  $("#guide-next").disabled = index === etapes.length - 1;
  $("#guide-progress-bar").style.width = `${(index + 1) / etapes.length * 100}%`;
  document.querySelector(".guide-progress").setAttribute("aria-valuenow", String(index + 1));
  document.querySelectorAll("[data-guide-index]").forEach((bouton) => {
    const actif = Number(bouton.dataset.guideIndex) === index;
    bouton.classList.toggle("active", actif);
    if (actif) bouton.setAttribute("aria-current", "step");
    else bouton.removeAttribute("aria-current");
  });
}

function remplirCollections(collections) {
  const select = $("#collection-select");
  const selection = select.value;
  select.innerHTML = collections.map((item) => `<option value="${proteger(item.nom)}">${proteger(item.libelle)} · ${proteger(item.nom)}</option>`).join("");
  if (collections.some((item) => item.nom === selection)) select.value = selection;
}

function valeurCellule(document, cle) {
  const valeur = document[cle];
  if (valeur === null || valeur === undefined || valeur === "") return "—";
  if (typeof valeur === "boolean") return valeur ? "Oui" : "Non";
  if (cle === "category") return categorieLisible(valeur);
  if (["montant", "discounted_line_total", "discountedTotal", "price"].includes(cle) && typeof valeur === "number") return montant.format(valeur);
  if (typeof valeur === "object") return JSON.stringify(valeur);
  return String(valeur);
}

function afficherTableau(resultat) {
  const champs = colonnes[resultat.collection] || [["_id", "Identifiant"]];
  $("#document-count").textContent = nombre.format(resultat.total);
  $("#table-head").innerHTML = `<tr>${champs.map((champ) => `<th scope="col">${proteger(champ[1])}</th>`).join("")}<th scope="col"><span class="sr-only">Détail</span></th></tr>`;
  etat.documents = resultat.documents;
  $("#table-body").innerHTML = resultat.documents.length ? resultat.documents.map((document, index) => `
    <tr>${champs.map(([cle]) => {
      if (cle === "statut") {
        const info = statutInfo(document.statut);
        return `<td><span class="table-pill ${info.classe}">${proteger(info.singulier)}</span></td>`;
      }
      return `<td>${proteger(valeurCellule(document, cle))}</td>`;
    }).join("")}<td><button class="detail-button" type="button" data-document="${index}">Voir détail</button></td></tr>`).join("") : `<tr><td class="placeholder" colspan="${champs.length + 1}">Aucun document trouvé.</td></tr>`;
  const debut = resultat.total ? (resultat.page - 1) * resultat.par_page + 1 : 0;
  const fin = Math.min(resultat.page * resultat.par_page, resultat.total);
  $("#page-info").textContent = `${nombre.format(debut)}–${nombre.format(fin)} sur ${nombre.format(resultat.total)} documents`;
  $("#previous-page").disabled = resultat.page <= 1;
  $("#next-page").disabled = fin >= resultat.total;
}

async function chargerCollection() {
  const selection = $("#collection-select").value;
  if (!selection) return;
  const requete = ++etat.derniereRequete;
  const parametres = new URLSearchParams({ page: String(etat.page), q: etat.recherche });
  try {
    const resultat = await chargerJson(`/api/collection/${encodeURIComponent(selection)}?${parametres}`);
    if (requete === etat.derniereRequete) afficherTableau(resultat);
  } catch (erreur) {
    if (requete !== etat.derniereRequete) return;
    $("#table-body").innerHTML = `<tr><td class="placeholder" colspan="7">${proteger(erreur.message)}</td></tr>`;
  }
}

async function actualiser() {
  const bouton = $("#refresh-button");
  bouton.disabled = true;
  try {
    const donnees = await chargerJson("/api/vue-ensemble");
    etat.donnees = donnees;
    actualiserConnexion(true);
    $("#empty-box").hidden = donnees.lignes_commandes > 0 && donnees.paiements > 0;
    afficherIndicateurs(donnees);
    afficherCategories();
    afficherPaiements(donnees);
    afficherEvolution(donnees);
    afficherClients(donnees);
    afficherGuide();
    remplirCollections(donnees.collections);
    await chargerCollection();
  } catch (erreur) {
    actualiserConnexion(false, erreur.message);
    $("#empty-box").hidden = true;
    $("#updated-at").textContent = "Données non actualisées";
  } finally {
    bouton.disabled = false;
  }
}

$("#refresh-button").addEventListener("click", actualiser);
document.querySelectorAll(".segment").forEach((bouton) => bouton.addEventListener("click", () => {
  etat.metrique = bouton.dataset.metric;
  document.querySelectorAll(".segment").forEach((element) => {
    const actif = element === bouton;
    element.classList.toggle("active", actif);
    element.setAttribute("aria-pressed", String(actif));
  });
  afficherCategories();
}));
$("#all-categories").addEventListener("click", () => { etat.toutesCategories = !etat.toutesCategories; afficherCategories(); });
document.querySelectorAll("[data-guide-index]").forEach((bouton) => bouton.addEventListener("click", () => {
  etat.etapeGuide = Number(bouton.dataset.guideIndex);
  afficherGuide();
}));
$("#guide-prev").addEventListener("click", () => { etat.etapeGuide -= 1; afficherGuide(); });
$("#guide-next").addEventListener("click", () => { etat.etapeGuide += 1; afficherGuide(); });
$("#collection-select").addEventListener("change", () => { etat.page = 1; etat.recherche = ""; $("#search-input").value = ""; chargerCollection(); });
let delaiRecherche;
$("#search-input").addEventListener("input", (event) => {
  clearTimeout(delaiRecherche);
  delaiRecherche = setTimeout(() => { etat.recherche = event.target.value.trim(); etat.page = 1; chargerCollection(); }, 250);
});
$("#previous-page").addEventListener("click", () => { if (etat.page > 1) { etat.page -= 1; chargerCollection(); } });
$("#next-page").addEventListener("click", () => { etat.page += 1; chargerCollection(); });
$("#table-body").addEventListener("click", (event) => {
  const bouton = event.target.closest("[data-document]");
  if (!bouton) return;
  const document = etat.documents[Number(bouton.dataset.document)];
  $("#document-detail").textContent = JSON.stringify(document, null, 2);
  $("#document-dialog").showModal();
});
$("#close-dialog").addEventListener("click", () => $("#document-dialog").close());
function synchroniserNavigation() {
  const section = window.location.hash || "#accueil";
  document.querySelectorAll(".nav-link").forEach((lien) => {
    const actif = lien.getAttribute("href") === section;
    lien.classList.toggle("active", actif);
    if (actif) lien.setAttribute("aria-current", "location");
    else lien.removeAttribute("aria-current");
  });
}

window.addEventListener("hashchange", synchroniserNavigation);
synchroniserNavigation();
afficherGuide();
actualiser();
setInterval(actualiser, 60000);
