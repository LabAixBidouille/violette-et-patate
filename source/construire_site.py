#!/usr/bin/env python3
"""Construit index.html à partir de source/texte.md.

Le moteur Harlowe (repris au départ du site de La Lune de Rambo) est conservé tel quel dans
index.html : seules les pages et la feuille de style du livre sont régénérées.

Usage, depuis la racine du dépôt : python3 source/construire_site.py
"""
import html
import re
import uuid
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
TEXTE = RACINE / "source" / "texte.md"
SORTIE = RACINE / "index.html"
NOINDEX = '<meta name="robots" content="noindex, nofollow, noarchive">'
# Favicon : les lunettes violettes de Violette, dessinées par Manon
FAVICON = ('<link rel="icon" type="image/png" sizes="48x48" href="images/favicon-48.png">'
           '<link rel="icon" type="image/png" sizes="180x180" href="images/favicon.png">'
           '<link rel="apple-touch-icon" href="images/favicon.png">')

TITRE = "Violette et Patate"
AUTRICES = "Eva et Brune"

SYNOPSIS = (
    "Violette a dix ans, deux tresses et des lunettes qui arrêtent le temps. Son passe-temps "
    "préféré ? Faire des bêtises, évidemment !\n\n"
    "Mais quand elle rencontre un corbeau grincheux et Patate, un bébé venu de la Lune, l'aventure "
    "prend un drôle de tournant… Entre diamants volés, tartes brûlées et sucette extraordinaire, "
    "une chose est sûre : le calme n'est pas près de revenir !"
)

# Texte écrit par Manon le 03/11/2026, modèle commun aux livres de l'atelier ; seule la phrase sur le
# genre change d'un livre à l'autre
CONTEXTE = [
    "En octobre 2026, le L.A.B a animé l’atelier « La quête du curry, une histoire dont tu es le héros » "
    "dans les bibliothèques Méjanes d’Aix-en-Provence. Les enfants ont été accompagnés dans la création "
    "d’un récit complet, depuis l’invention des personnages jusqu’à la construction d’une intrigue "
    "reliant les différentes étapes de leur aventure.",
    "Nous leur avons proposé d’introduire une part de hasard dans leur récit. Le résultat d’un lancer de "
    "dé pouvait modifier le déroulement de certains passages et conduire le lecteur vers un chapitre ou "
    "un autre.",
    "Les enfants ont ainsi exploré, sans écran, des notions liées à la pensée computationnelle, une "
    "manière de décomposer un problème et d’organiser les étapes pour le résoudre. Ils ont formulé des "
    "règles de type « si… alors… », créé des embranchements et réfléchi à la façon dont les chemins se "
    "rejoignent pour former une histoire cohérente.",
    "Eva et Brune ont choisi d’inventer une histoire drôle. Un défi pour une histoire à embranchements, "
    "puisque les gags doivent rester drôles et les chutes tomber juste, quel que soit le chemin emprunté.",
    "L’atelier ne durait que deux heures, mais nous tenions à offrir à chaque enfant un livre "
    "complet. Le L.A.B a donc prolongé et mis en forme leur récit à l’aide d’outils numériques, "
    "et l’intelligence artificielle a notamment permis d’aboutir à une histoire achevée et "
    "agréable à lire. À son origine, il y a avant tout les idées et les personnages d’Eva et de "
    "Brune.",
]
# Une phrase de leur fiche récit, à peine remise au propre
CITATION = ("Le corbeau a un pouvoir et quand Violette arrête le temps, il bouge encore pour protéger ses "
            "diamants.")

CSS = """
@font-face { font-family: "Luckiest Guy"; font-style: normal; font-weight: 400; font-display: swap; src: url("fonts/LuckiestGuy.woff2") format("woff2"); }
@font-face { font-family: "Nunito"; font-style: normal; font-weight: 400 800; font-display: swap; src: url("fonts/Nunito.woff2") format("woff2"); }
@font-face { font-family: "Nunito"; font-style: italic; font-weight: 400; font-display: swap; src: url("fonts/Nunito-italique.woff2") format("woff2"); }
@font-face { font-family: "Gochi Hand"; font-style: normal; font-weight: 400; font-display: swap; src: url("fonts/GochiHand.woff2") format("woff2"); }

/* Couleurs des illustrations : violet du sweat et des lunettes, orange vif pour les accents,
   menthe du bol, jaune de l'étoile, fond lavande */
:root {
  --violet: #7b4fb0;
  --violet-fonce: #5b3590;
  --orange: #ff6a00;
  --menthe: #3f9c80;
  --menthe-clair: #a8dcc9;
  --jaune: #f4c430;
  --lavande: #efe7f8;
  --encre: #2b2f3a;
  --gris: #5b6272;
  --papier: #ffffff;
}
html, body, tw-story {
  background-color: var(--papier);
  color: var(--encre);
}
tw-story {
  font-family: "Nunito", "Trebuchet MS", sans-serif;
  font-size: 1.02em;
  line-height: 1.7;
  padding: 4em 1.25em 4em;
}
tw-passage {
  max-width: 1180px;
  margin: 0 auto;
}

/* Pages de lecture : le texte à gauche, l'illustration à droite, comme pour La Lune de Rambo */
.page {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
  gap: 2em;
  align-items: start;
}
.cote {
  position: sticky;
  top: 1.5em;
  margin-top: 2.5em;
}
.illustration img {
  display: block;
  width: 100%;
  max-height: 85vh;
  object-fit: contain;
  mix-blend-mode: multiply;
}
@media (max-width: 800px) {
  .page { grid-template-columns: minmax(0, 1fr); gap: 1.2em; }
  /* Sur téléphone : l'illustration au-dessus du texte */
  .cote { position: static; order: -1; margin-top: 0; }
}
tw-sidebar { display: none; }
/* Harlowe met « overflow: hidden » sur tw-story, ce qui empêche la colonne de droite de rester
   visible au défilement ; « clip » coupe pareil sans créer de zone de défilement */
tw-story { overflow: clip; }

/* Titres de chapitre : le numéro écrit à la main, le titre en lettres de bande dessinée */
.chapitre {
  font-size: 1em;
  font-weight: 400;
  margin: 0 0 1.1em;
  line-height: 1.05;
}
.chapitre .numero {
  display: inline-block;
  font-family: "Gochi Hand", cursive;
  font-size: 1.35em;
  color: #ffffff;
  background-color: var(--orange);
  padding: 0.05em 0.6em 0.1em;
  border-radius: 0.4em;
  transform: rotate(-3deg);
  margin-bottom: 0.75em;
}
.chapitre .titre {
  display: block;
  font-family: "Luckiest Guy", "Impact", sans-serif;
  font-weight: 400;
  font-size: 2.1em;
  letter-spacing: 0.02em;
  color: var(--violet);
  text-shadow: 2px 2px 0 var(--orange);
}

/* Page de garde */
/* La couverture tient dans l'écran : marges réduites et tailles qui suivent la hauteur de l'écran */
tw-story:has(.garde) { padding-top: 1em; padding-bottom: 1em; }
.garde {
  min-height: calc(100vh - 2.2em);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: clamp(0.8em, 3vh, 2em);
}
.garde-entete {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}
.garde-corps {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
  gap: 3em;
  align-items: center;
}
.garde-image img {
  display: block;
  width: 100%;
  max-height: 60vh;
  object-fit: contain;
  height: auto;
  mix-blend-mode: multiply;
}
.garde-texte {
  display: flex;
  flex-direction: column;
  /* Même écart entre le résumé, le séparateur, le bouton Commencer et les deux petits boutons */
  gap: clamp(1.2em, 3.6vh, 2.1em);
  text-align: center;
}
@media (max-width: 800px) {
  .garde { min-height: 0; }
  .garde-corps { grid-template-columns: minmax(0, 1fr); gap: 1em; }
  .garde-image img { max-height: none; }
}
.garde .surtitre {
  font-family: "Gochi Hand", cursive;
  font-size: 1.4em;
  color: var(--gris);
}
.garde .grand-titre {
  font-family: "Luckiest Guy", "Impact", sans-serif;
  font-size: clamp(2.2em, 7vh, 4.2em);
  line-height: 1;
  color: var(--violet);
  text-shadow: 4px 4px 0 var(--orange);
  margin: 0.15em 0 0.1em;
  transform: rotate(-2deg);
}
.garde .nom-auteur {
  font-family: "Gochi Hand", cursive;
  font-size: clamp(1.4em, 4vh, 2em);
  color: var(--orange);
}
.garde .synopsis {
  margin: 0 auto;
  max-width: 34em;
  font-size: 1.08em;
  line-height: 1.6;
}
.garde .commencer tw-link, .garde .commencer .enchantment-link {
  display: inline-block;
  font-family: "Luckiest Guy", "Impact", sans-serif;
  font-size: 1.15em;
  letter-spacing: 0.03em;
  color: #ffffff;
  background-color: var(--orange);
  border: none;
  border-radius: 999px;
  padding: 0.5em 1.3em 0.35em;
  box-shadow: 0 4px 0 var(--violet);
}
.garde .commencer tw-link:hover, .garde .commencer .enchantment-link:hover {
  color: #ffffff;
  transform: translateY(2px);
  box-shadow: 0 2px 0 var(--violet);
}
.garde .secondaires {
  /* compense l'ombre du bouton Commencer, pour que l'écart paraisse le même à l'œil */
  margin-top: 4px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.8em 1.4em;
}

/* Petits boutons secondaires */
.secondaires tw-link, .secondaires .enchantment-link {
  display: inline-block;
  font-size: 0.85em;
  color: var(--violet);
  border: 2px solid var(--violet);
  border-radius: 999px;
  padding: 0.3em 1em;
}
.secondaires tw-link:hover, .secondaires .enchantment-link:hover {
  background-color: var(--violet);
  color: #ffffff;
}

/* Lien Couverture : discret, en haut à gauche, au-dessus du numéro de chapitre */
.retour {
  margin: 0 auto 1.2em;
  text-align: left;
}
.retour tw-link, .retour .enchantment-link,
.lien-retour tw-link, .lien-retour .enchantment-link {
  font-size: 0.9em;
  font-weight: 600;
  color: var(--gris);
}
.retour tw-link::before, .lien-retour tw-link::before { content: "← "; }
.retour tw-link:hover, .retour .enchantment-link:hover,
.lien-retour tw-link:hover, .lien-retour .enchantment-link:hover { color: var(--violet); }
.contexte .lien-retour { display: block; margin-bottom: 1em; }

/* Le lancer de dé */
.de .consigne {
  display: block;
  font-family: "Gochi Hand", cursive;
  font-size: 1.35em;
  line-height: 1.25;
  color: var(--encre);
  margin-bottom: 0.5em;
}
/* Choix en liste à puces, comme pour La Lune de Rambo */
.choix {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.45em;
}
.choix > *::before {
  content: "•";
  color: var(--orange);
  font-weight: 800;
  margin-right: 0.55em;
}
.choix tw-link, .choix .enchantment-link {
  color: var(--violet);
  font-weight: 700;
  border-bottom: 1.5px solid rgba(123, 79, 176, 0.35);
}
.choix tw-link:hover, .choix .enchantment-link:hover {
  color: var(--violet-fonce);
  border-bottom-color: var(--orange);
}
.elan > *::before { content: none; }
.suite {
  margin-top: 0.8em;
}

/* Séparateur : les lunettes de Violette entre deux traits */
.separateur {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.7em;
  margin: 1.5em 0 1em;
}
.separateur::after { transform: scaleX(-1); }
.separateur::before, .separateur::after {
  content: "";
  width: 6.5em;
  height: 22px;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='26' height='22'%3E%3Cpath d='M0 16 C8 16 16 14 16 8 C16 2 9 2 9 8 C9 14 17 16 26 16' fill='none' stroke='%233f9c80' stroke-width='2.5' stroke-linecap='round'/%3E%3C/svg%3E") repeat-x left center;
}
.separateur .lunettes {
  width: 3.2em;
  height: 1.25em;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 24'%3E%3Cg fill='none' stroke='%237b3fa0' stroke-width='3' stroke-linecap='round'%3E%3Ccircle cx='17' cy='14' r='8'/%3E%3Ccircle cx='47' cy='14' r='8'/%3E%3Cpath d='M25 13 Q32 8 39 13'/%3E%3Cpath d='M9 12 L3 6'/%3E%3Cpath d='M55 12 L61 6'/%3E%3C/g%3E%3C/svg%3E") no-repeat center / contain;
}
.garde .separateur { margin: 0; }

/* Bouton d'élan, quand Violette entraîne le lecteur */
.elan {
  align-items: center;
  margin-top: 2.2em;
}
.elan tw-link, .elan .enchantment-link {
  display: inline-block;
  font-family: "Luckiest Guy", "Impact", sans-serif;
  font-weight: 400;
  font-size: 1.15em;
  letter-spacing: 0.03em;
  color: #ffffff;
  background-color: var(--orange);
  border: none;
  border-radius: 999px;
  padding: 0.5em 1.3em 0.35em;
  box-shadow: 0 4px 0 var(--violet);
  transform: rotate(-2deg);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
/* Au survol : il bascule, grossit un peu, et un liseré blanc puis orange apparaît autour */
.elan tw-link:hover, .elan .enchantment-link:hover {
  color: #ffffff;
  background-color: var(--orange);
  transform: rotate(2deg) scale(1.06);
  box-shadow: 0 0 0 3px #ffffff, 0 0 0 5px var(--orange), 0 6px 0 3px var(--violet);
}

/* Dé à lancer sur le site : à droite du bloc consigne et choix, face blanche, contour violet,
   points orange ; il montre une face au repos et ne choisit jamais à la place du lecteur */
.de {
  display: flex;
  align-items: center;
  gap: 1.6em;
}
.de-texte { flex: 1; min-width: 0; }
/* Flèche dessinée à la main qui montre le dé */
.fleche-de { flex: none; width: 3.2em; height: auto; margin-right: -0.6em; transform: translateY(-0.4em); }
/* Le résultat s'affiche sous le dé sans compter dans la hauteur : le dé reste fixe,
   exactement au milieu du bloc consigne et choix */
.lancer {
  flex: none;
  position: relative;
  display: flex;
}
.de-virtuel {
  width: 4.6em;
  height: 4.6em;
  padding: 0.5em;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(3, 1fr);
  background: #ffffff;
  border: 3px solid var(--violet);
  border-radius: 0.8em;
  box-shadow: 0 4px 0 var(--orange);
  cursor: pointer;
  transform: rotate(-5deg);
  transition: transform 0.15s ease;
}
.de-virtuel:hover { transform: rotate(5deg); }
.de-virtuel.roule { animation: roule 0.3s linear infinite; }
@keyframes roule {
  0% { transform: rotate(0deg) translateY(0); }
  50% { transform: rotate(180deg) translateY(-3px); }
  100% { transform: rotate(360deg) translateY(0); }
}
.de-virtuel i {
  width: 0.8em;
  height: 0.8em;
  border-radius: 50%;
  background: var(--orange);
  place-self: center;
  visibility: hidden;
}
/* Avant le premier lancer : un point d'interrogation orange, centré comme les points */
.de-virtuel { position: relative; }
.de-virtuel[data-face="0"]::after {
  content: "?";
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding-top: 0.15em;
  font-family: "Luckiest Guy", "Impact", sans-serif;
  font-size: 2.6em;
  line-height: 1;
  color: var(--orange);
}
.de-virtuel[data-face="1"] i:nth-child(5),
.de-virtuel[data-face="2"] i:is(:nth-child(1), :nth-child(9)),
.de-virtuel[data-face="3"] i:is(:nth-child(1), :nth-child(5), :nth-child(9)),
.de-virtuel[data-face="4"] i:is(:nth-child(1), :nth-child(3), :nth-child(7), :nth-child(9)),
.de-virtuel[data-face="5"] i:is(:nth-child(1), :nth-child(3), :nth-child(5), :nth-child(7), :nth-child(9)),
.de-virtuel[data-face="6"] i:is(:nth-child(1), :nth-child(3), :nth-child(4), :nth-child(6), :nth-child(7), :nth-child(9)) {
  visibility: visible;
}
.resultat {
  position: absolute;
  top: calc(100% + 0.6em);
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  font-family: "Gochi Hand", cursive;
  font-size: 1.1em;
  color: var(--gris);
  text-align: center;
}
@media (max-width: 600px) {
  .de { gap: 0.6em; }
  .fleche-de { width: 2.2em; }
  .de-virtuel { width: 3.6em; height: 3.6em; padding: 0.4em; }
  .de-virtuel i { width: 0.6em; height: 0.6em; }
  .de-virtuel[data-face="0"]::after { font-size: 2em; }
}

/* Fins */
.fin {
  margin-top: 0.6em;
  text-align: center;
}
.fin .mot-fin {
  display: block;
  font-family: "Luckiest Guy", "Impact", sans-serif;
  font-size: 2.6em;
  color: var(--menthe);
  transform: rotate(-3deg);
}

/* Phrase mise en avant dans le texte */
.appel {
  font-family: "Gochi Hand", cursive;
  font-size: 1.4em;
  color: var(--orange);
}

/* Page « Comment est née cette histoire » : texte court centré, une phrase des autrices, puis leurs
   fiches posées sur une table, en miniatures cliquables */
.contexte { font-size: 0.95em; text-align: center; }
.contexte .lien-retour { text-align: left; }
.contexte h1 {
  line-height: 1.1;
  font-family: "Luckiest Guy", "Impact", sans-serif;
  font-weight: 400;
  font-size: 2.4em;
  color: var(--violet);
  text-shadow: 3px 3px 0 var(--orange);
  margin: 0.3em 0 0.2em;
}
.contexte-texte { max-width: 38em; margin: 0 auto; }
.citation {
  max-width: 30em;
  margin: 2em auto;
  font-family: "Gochi Hand", cursive;
  font-size: 1.55em;
  line-height: 1.35;
  color: var(--violet);
  transform: rotate(-1.5deg);
}
.citation .source {
  display: block;
  margin-top: 0.4em;
  font-family: "Nunito", sans-serif;
  font-size: 0.55em;
  color: var(--gris);
}
.table-fiches {
  margin: 2.6em auto 0;
  max-width: 62em;
  padding: 1.8em 1.5em 1.8em;
  background: var(--lavande);
  border-radius: 18px;
}
.table-fiches .titre-table {
  display: block;
  font-family: "Luckiest Guy", "Impact", sans-serif;
  font-size: 1.35em;
  color: var(--violet);
  margin-bottom: 1.2em;
}
.miniatures {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 2.4em;
}
.miniatures figure { margin: 0; }
.miniatures figcaption {
  margin-top: 0.8em;
  font-family: "Gochi Hand", cursive;
  font-size: 1.15em;
  color: var(--gris);
}
.miniature { display: block; padding: 0; border: none; background: none; cursor: zoom-in; }
.miniature img {
  display: block;
  height: 16em;
  width: auto;
  border-radius: 4px;
  box-shadow: 0 3px 12px rgba(43, 47, 58, 0.22);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.miniatures figure:nth-child(1) img { transform: rotate(-3deg); }
.miniatures figure:nth-child(2) img { transform: rotate(1deg); }
.miniatures figure:nth-child(3) img { transform: rotate(3deg); }
.miniatures .miniature:hover img { transform: rotate(0) scale(1.05); box-shadow: 0 0 0 3px var(--orange), 0 8px 20px rgba(43, 47, 58, 0.28); }
.contexte .credits { display: block; margin-top: 1.6em; font-size: 0.92em; color: var(--gris); }
.contexte .secondaires { display: flex; justify-content: center; margin-top: 1.4em; }
/* Fiche ouverte en grand par-dessus la page ; un clic n'importe où la referme */
.agrandi {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2vh 2vw;
  background: rgba(43, 30, 70, 0.85);
  cursor: zoom-out;
}
.agrandi img { max-width: 100%; max-height: 96vh; border-radius: 4px; box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4); }
@media (max-width: 600px) {
  .miniature img { height: 11em; }
}

/* Page de l'arbre : le titre centré en haut, l'arbre dessous */
.arbre .lien-retour { display: block; }
.arbre-tete { text-align: center; margin-bottom: 1.5em; }
.arbre h1 {
  font-family: "Luckiest Guy", "Impact", sans-serif;
  font-weight: 400;
  font-size: 2.4em;
  line-height: 1.1;
  color: var(--violet);
  text-shadow: 3px 3px 0 var(--orange);
  margin: 0;
}
.arbre .arbre-sous-titre {
  display: block;
  font-family: "Gochi Hand", cursive;
  font-size: 1.3em;
  color: var(--gris);
  margin: 0.3em 0 1em;
}
.arbre img { display: block; width: 100%; max-width: 760px; height: auto; margin: 0 auto; }

/* Liens dans le texte */
tw-link, .enchantment-link {
  color: var(--violet);
  font-weight: 700;
  text-decoration: none;
}
tw-link:hover, .enchantment-link:hover { color: var(--violet-fonce); }

@media (max-width: 600px) {
  tw-story { font-size: 0.98em; }
  .garde .grand-titre { font-size: 2.9em; }
  .chapitre .titre { font-size: 1.7em; }
}

/* Écrans peu hauts : on resserre le résumé et les espacements pour que tout tienne */
@media (max-height: 620px) and (min-width: 801px) {
  tw-story:has(.garde) { padding-top: 0.6em; padding-bottom: 0.6em; }
  .garde { min-height: calc(100vh - 1.4em); gap: 0.6em; }
  .garde .synopsis { font-size: 0.95em; line-height: 1.45; }
  .garde-texte { gap: 0.85em; }
  .garde-image img { max-height: 54vh; }
}
"""


def e(texte):
    return html.escape(texte, quote=True)


def lire_chapitres():
    blocs = re.split(r"^## ", TEXTE.read_text(encoding="utf-8"), flags=re.M)[1:]
    chapitres = []
    for bloc in blocs:
        lignes = bloc.strip().split("\n")
        titre_complet = lignes[0].strip()
        numero, titre = titre_complet.split(". ", 1)
        nom = numero
        paragraphes = [p.strip() for p in "\n".join(lignes[1:]).split("\n\n") if p.strip()]
        chapitres.append({"nom": nom, "numero": numero, "titre": titre, "paragraphes": paragraphes})
    return chapitres


SEPARATEUR = '<div class="separateur"><span class="lunettes"></span></div>'


DE_VIRTUEL = (
    '<svg class="fleche-de" viewBox="0 0 60 40" aria-hidden="true"><g fill="none" stroke="#ff6a00" '
    'stroke-width="3" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M4 30 C16 34 34 30 48 16"/><path d="M38 14 L49 15 L47 26"/></g></svg>'
    '<div class="lancer"><button class="de-virtuel" type="button" data-face="0" '
    'aria-label="Lancer le dé">' + "<i></i>" * 9 + '</button>'
    '<span class="resultat" aria-live="polite"></span></div>'
)

# Script commun à toutes les pages : fait rouler le dé puis affiche la face tirée, sans choisir
SCRIPT_DE = """
document.addEventListener('click', function (evenement) {
  var de = evenement.target.closest('.de-virtuel');
  if (!de || de.classList.contains('roule')) return;
  var resultat = de.parentNode.querySelector('.resultat');
  var face = 1 + Math.floor(Math.random() * 6);
  var etapes = 0;
  de.classList.add('roule');
  resultat.textContent = '';
  var minuterie = setInterval(function () {
    de.setAttribute('data-face', 1 + Math.floor(Math.random() * 6));
    etapes += 1;
    if (etapes >= 8) {
      clearInterval(minuterie);
      de.setAttribute('data-face', face);
      de.classList.remove('roule');
      resultat.textContent = 'Le dé affiche ' + face + '.';
    }
  }, 75);
});

// Page de contexte : une miniature s'ouvre en grand, un clic referme
document.addEventListener('click', function (evenement) {
  var ouvert = document.querySelector('.agrandi');
  if (ouvert) { ouvert.remove(); return; }
  var miniature = evenement.target.closest('.miniature');
  if (!miniature) return;
  var fond = document.createElement('div');
  fond.className = 'agrandi';
  var image = document.createElement('img');
  image.src = miniature.querySelector('img').src;
  image.alt = miniature.querySelector('img').alt;
  fond.appendChild(image);
  document.body.appendChild(fond);
});
document.addEventListener('keydown', function (evenement) {
  var ouvert = document.querySelector('.agrandi');
  if (ouvert && evenement.key === 'Escape') ouvert.remove();
});
"""

def lien(texte, cible):
    return f"[[{texte}->{cible}]]"


def passage_chapitre(ch):
    corps = []
    tirage = any(p.startswith("**Lance le dé") for p in ch["paragraphes"])
    consigne = None
    choix = []
    fin = False
    appel = False
    for p in ch["paragraphes"]:
        if p.startswith("- "):
            for ligne in p.split("\n"):
                texte, cible = ligne[2:].rsplit(" -> ", 1)
                choix.append(lien(texte, f"Chapitre {cible}"))
        elif p == "FIN":
            fin = True
        elif p.startswith("**") and p.endswith("**"):
            interieur = p[2:-2]
            if interieur.startswith("Lance le dé") or interieur.startswith("Te souviens-tu"):
                consigne = interieur
            else:
                corps.append(SEPARATEUR + f'<span class="appel">{interieur}</span>')
                appel = True
        else:
            corps.append(p)

    suite = []
    if not appel:
        suite.append(SEPARATEUR)
    if consigne:
        # Sur les vrais tirages, un dé à lancer à droite du bloc consigne et choix ; il montre la face sans choisir
        lancer = DE_VIRTUEL if tirage else ""
        if tirage:
            # Sur le site, on lance le dé en cliquant dessus : la consigne le dit, une flèche le montre
            consigne = consigne.replace("Lance le dé", "Clique sur le dé", 1)
        suite.append(f'<div class="de"><div class="de-texte"><span class="consigne">{consigne}</span>'
                     f'<div class="choix">{"".join(choix)}</div></div>{lancer}</div>')
    elif choix:
        # Un renvoi seul, sans lancer de dé, devient un gros bouton comme « Montre-moi tes bêtises ! »
        suite.append(f'<div class="choix suite elan">{"".join(choix)}</div>')
    if fin:
        suite.append('<div class="fin"><span class="mot-fin">FIN</span>'
                     f'<div class="secondaires">{lien("Comment est née cette histoire", "Comment est née cette histoire")}</div></div>')
    texte = ('<div class="texte">'
             f'<h1 class="chapitre"><span class="numero">{ch["numero"]}</span>'
             f'<span class="titre">{ch["titre"]}</span></h1>'
             + "\n\n".join(corps) + "".join(suite) + "</div>")
    # Colonne de droite : l'illustration, qui suit la lecture au défilement
    image = f"images/chapitres/{illustration(ch['nom'])}.jpg"
    cote = ""
    if (RACINE / image).exists():
        cote = f'<div class="cote"><div class="illustration"><img src="{image}" alt="{ch["titre"]}"></div></div>'
    return f'<div class="page">{texte}{cote}</div>'


def illustration(nom):
    """Nom du fichier d'illustration : prologue, chapitre-01, chapitre-02…"""
    return "prologue" if nom == "Prologue" else f"chapitre-{int(nom.split()[-1]):02d}"


def passage_garde():
    return (
        # En haut, centrés : surtitre, titre et autrices ; dessous, l'image à gauche et le texte à droite
        '<div class="garde"><div class="garde-entete">'
        '<span class="surtitre">Une histoire dont le lecteur est le héros</span>'
        f'<div class="grand-titre">{TITRE}</div>'
        f'<span class="nom-auteur">{AUTRICES}</span></div>'
        '<div class="garde-corps"><div class="garde-image"><img src="images/couverture.jpg" '
        'alt="Violette part vers la forêt, sous une étoile filante, pendant que le corbeau l\'attend"></div>'
        f'<div class="garde-texte"><div class="synopsis">{SYNOPSIS}</div>{SEPARATEUR}'
        f'<div class="commencer">{lien("Commencer l'histoire", "Prologue")}</div>'
        f'<div class="secondaires">{lien("Comment est née cette histoire", "Comment est née cette histoire")} '
        f'{lien("L\'arbre de l\'histoire", "L\'arbre de l\'histoire")}</div>'
        "</div></div></div>"
    )


def miniature(fichier, legende, description):
    return (f'<figure><button class="miniature" type="button" aria-label="Agrandir {description}">'
            f'<img src="images/fiches/{fichier}" alt="{description}"></button>'
            f'<figcaption>{legende}</figcaption></figure>')


def passage_contexte():
    return (
        '<div class="contexte"><span class="lien-retour">[[Couverture->Page de garde]]</span>\n'
        f'<h1>Comment est née cette histoire</h1>{SEPARATEUR}'
        '<div class="contexte-texte">'
        + "\n\n".join(CONTEXTE[:4])
        + f'<div class="citation">« {CITATION} »<span class="source">Eva et Brune, sur leur fiche récit</span></div>'
        + CONTEXTE[4]
        + '</div><div class="table-fiches"><span class="titre-table">Les fiches de l’atelier</span>'
        '<div class="miniatures">'
        + miniature("fiche_recit.jpg", "Le récit", "la fiche récit, par Eva et Brune")
        + miniature("fiche_personnage_patate.jpg", "Une fiche personnage", "la fiche personnage de Patate")
        + miniature("fiche_situation_4.jpg", "Une fiche à embranchement", "la fiche situation n° 4, avec ses choix au dé")
        + '</div></div>'
        + '<span class="credits">Une histoire d’Eva et de Brune.\nRéalisation du livre : '
        "Laboratoire d’Aix-périmentation et de Bidouille.</span>"
        + f'<div class="secondaires">{lien("Commencer le livre", "Prologue")}</div>\n</div>'
    )


def passage_arbre():
    # Page simple : le titre centré en haut, l'arbre dessous
    return (
        f'<div class="arbre"><span class="lien-retour">{lien("Couverture", "Page de garde")}</span>'
        f'<div class="arbre-tete"><h1>{TITRE}</h1>'
        f'<span class="arbre-sous-titre">Tous les chemins de l\'histoire imaginée par {AUTRICES}</span></div>'
        '<img src="images/arbre.svg" alt="L\'arbre de toutes les branches de l\'histoire"></div>'
    )


def construire():
    modele = SORTIE.read_text(encoding="utf-8")
    debut = modele[: modele.index("<tw-storydata")]
    moteur = modele[modele.index("</tw-storydata>"):]
    if NOINDEX not in debut:
        debut = debut.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + NOINDEX)
    # Icônes : on retire celles qui traînent (héritées de Rambo ou d'une construction précédente)
    # puis on remet le favicon du livre
    debut = re.sub(r"<link rel=\"(?:icon|apple-touch-icon)\"[^>]*>", "", debut)
    debut = debut.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + FAVICON)
    debut = debut.replace("<title>La Lune de Rambo</title>", f"<title>{TITRE}</title>")
    moteur = moteur.replace("JavaScript needs to be enabled to play La Lune de Rambo.",
                            f"JavaScript doit être activé pour lire {TITRE}.")
    debut = debut.replace("JavaScript needs to be enabled to play La Lune de Rambo.",
                          f"JavaScript doit être activé pour lire {TITRE}.")

    passages = [
        ("Bouton couverture", "header",
         '(unless: (a: "Page de garde", "L\'arbre de l\'histoire", "Comment est née cette histoire") contains (passage:)\'s name)'
         '[<div class="retour">[[Couverture->Page de garde]]</div>]'),
        ("Page de garde", "", passage_garde()),
        ("Comment est née cette histoire", "", passage_contexte()),
        ("L'arbre de l'histoire", "", passage_arbre()),
    ]
    for ch in lire_chapitres():
        passages.append((ch["nom"], "", passage_chapitre(ch)))

    # Espaces insécables de la typographie française : un guillemet ou un deux-points ne se retrouve
    # jamais seul en début de ligne
    insecables = [("« ", "«\u00a0"), (" »", "\u00a0»"), (" :", "\u00a0:"), (" ?", "\u00a0?"),
                  (" !", "\u00a0!"), (" ;", "\u00a0;")]
    for i, (nom, tags, contenu) in enumerate(passages):
        if tags != "header":
            for avant, apres in insecables:
                contenu = contenu.replace(avant, apres)
            passages[i] = (nom, tags, contenu)

    noms = {p[0] for p in passages}
    for nom, _, contenu in passages:
        for cible in re.findall(r"->([^\]]+)\]\]", contenu):
            assert cible in noms, f"Lien cassé dans {nom} : {cible}"

    xml = [f'<tw-storydata name="{e(TITRE)}" startnode="2" creator="Twine" creator-version="2.12.1" '
           f'format="Harlowe" format-version="3.3.9" ifid="{str(uuid.uuid5(uuid.NAMESPACE_URL, TITRE)).upper()}" '
           'options="" tags="" zoom="1" hidden>',
           f'<style role="stylesheet" id="twine-user-stylesheet" type="text/twine-css">{CSS}</style>',
           '<script role="script" id="twine-user-script" type="text/twine-javascript">' + SCRIPT_DE + '</script>']
    for pid, (nom, tags, contenu) in enumerate(passages, start=1):
        xml.append(f'<tw-passagedata pid="{pid}" name="{e(nom)}" tags="{tags}" '
                   f'position="{pid * 150},0" size="100,100">{e(contenu)}</tw-passagedata>')
    SORTIE.write_text(debut + "".join(xml) + moteur, encoding="utf-8")
    print(f"{SORTIE} : {len(passages)} passages")


if __name__ == "__main__":
    construire()
