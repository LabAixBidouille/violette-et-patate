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

TITRE = "Violette et Patate"
AUTRICES = "Eva et Brune"

SYNOPSIS = (
    "Violette a dix ans, deux tresses et des lunettes qui arrêtent le temps. Elle s'en sert pour "
    "faire des bêtises, surtout pour faire brûler les tartes de toute la ville. Ce matin, elle part "
    "dans la forêt attraper un corbeau. Mais elle a oublié ses lunettes, le corbeau bouge dans le "
    "temps arrêté, et un bébé venu de la Lune lui a volé ses diamants. Qui va gagner : la farceuse "
    "ou le bébé ?"
)

CONTEXTE = [
    "Le mardi 27 octobre 2026, pendant les vacances d'automne, le L.A.B a animé l'atelier « Le livre "
    "dont tu es le héros » à la bibliothèque des Deux Ormes, l'une des bibliothèques Méjanes "
    "d'Aix-en-Provence. Huit enfants de 8 à 12 ans y ont inventé une histoire qui change selon les "
    "choix du lecteur, en l'écrivant situation par situation sur des fiches où chaque lancer de dé "
    "renvoie vers une autre situation. L'atelier est issu du projet européen Robots Meet Arts : "
    "derrière le récit, il s'agit de découvrir sans écran les notions qui structurent un programme "
    "informatique. Chaque lancer de dé est une condition, qui décide de la suite de l'histoire. "
    "Chaque choix ouvre un embranchement, et un chemin qui ramène à une situation déjà écrite forme "
    "une boucle.",
    "Écrire une telle histoire demande un travail créatif considérable. Il faut inventer un "
    "personnage et une quête, mais aussi penser l'histoire comme un réseau : prévoir à chaque étape "
    "plusieurs suites possibles, numéroter les situations, s'assurer que chaque chemin mène quelque "
    "part, et faire tenir tous ces fils ensemble sans perdre le sens du récit.",
    "Eva et Brune ont relevé ce défi à deux. Elles ont inventé Violette, une fille de dix ans dont "
    "les lunettes magiques arrêtent le temps, Patate, un bébé venu de la Lune dont la sucette se "
    "transforme en tout ce qu'il veut, et Mirette, une mamie qui raconte sa vie et prépare des "
    "tartes qui se mangent sans cuire. C'est à elles que l'on doit les lunettes qui viennent "
    "rejoindre Violette à pied, le corbeau qui bouge dans le temps arrêté pour protéger ses "
    "diamants, le concours de corde à sauter et ce bébé qui, une fois tombé, ne peut plus se "
    "relever, parce que c'est une patate.",
    "Pour leur histoire, Eva et Brune ont choisi l'humour. Avec //Violette et Patate//, elles vous "
    "présentent un récit comique, raconté par une héroïne farceuse qui arrête le temps pour faire "
    "des bêtises et finit par trouver, chez un bébé venu de la Lune, le complice idéal.",
    "Pour offrir à chaque enfant un livre achevé, dont il ou elle puisse être fier ou fière et avec "
    "lequel continuer à jouer, le L.A.B a prolongé chaque histoire à partir des idées de celles et "
    "ceux qui l'ont imaginée, puis l'a mise en forme, en s'aidant d'outils numériques, dont "
    "l'intelligence artificielle. Ce travail ne retire rien à celui des enfants : il s'appuie "
    "entièrement sur la créativité, l'imaginaire et les récits de celles et ceux qui ont participé "
    "à l'atelier.",
]

CSS = """
@font-face { font-family: "Luckiest Guy"; font-style: normal; font-weight: 400; font-display: swap; src: url("fonts/LuckiestGuy.woff2") format("woff2"); }
@font-face { font-family: "Nunito"; font-style: normal; font-weight: 400 800; font-display: swap; src: url("fonts/Nunito.woff2") format("woff2"); }
@font-face { font-family: "Nunito"; font-style: italic; font-weight: 400; font-display: swap; src: url("fonts/Nunito-italique.woff2") format("woff2"); }
@font-face { font-family: "Gochi Hand"; font-style: normal; font-weight: 400; font-display: swap; src: url("fonts/GochiHand.woff2") format("woff2"); }

/* Couleurs du LAB : orange pour l'énergie, bleu pour les titres, vert pour les fins */
:root {
  --orange: #fd7e14;
  --orange-clair: #fff1e3;
  --bleu: #356bac;
  --bleu-fonce: #244d80;
  --vert: #6c9e23;
  --encre: #2b2f3a;
  --gris: #5b6272;
  --papier: #fffdf8;
}
html, body, tw-story {
  background-color: var(--papier);
  color: var(--encre);
}
tw-story {
  font-family: "Nunito", "Trebuchet MS", sans-serif;
  font-size: 1.12em;
  line-height: 1.7;
  padding: 2.5em 1.25em 4em;
}
tw-passage {
  max-width: 42em;
  margin: 0 auto;
}
tw-sidebar { display: none; }

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
  color: var(--bleu);
  text-shadow: 3px 3px 0 var(--orange-clair);
}

/* Page de garde */
.garde {
  min-height: calc(100vh - 7em);
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: center;
}
.garde .surtitre {
  font-family: "Gochi Hand", cursive;
  font-size: 1.4em;
  color: var(--gris);
}
.garde .grand-titre {
  font-family: "Luckiest Guy", "Impact", sans-serif;
  font-size: 4.2em;
  line-height: 1;
  color: var(--orange);
  text-shadow: 4px 4px 0 var(--bleu);
  margin: 0.15em 0 0.1em;
  transform: rotate(-2deg);
}
.garde .nom-auteur {
  font-family: "Gochi Hand", cursive;
  font-size: 2em;
  color: var(--bleu);
}
.garde .synopsis {
  margin: 1.4em auto 1.6em;
  max-width: 34em;
  font-size: 0.98em;
}
.garde .commencer tw-link, .garde .commencer .enchantment-link {
  display: inline-block;
  font-family: "Luckiest Guy", "Impact", sans-serif;
  font-size: 1.5em;
  letter-spacing: 0.03em;
  color: #ffffff;
  background-color: var(--orange);
  border: none;
  border-radius: 999px;
  padding: 0.45em 1.4em 0.3em;
  box-shadow: 0 4px 0 var(--bleu);
}
.garde .commencer tw-link:hover, .garde .commencer .enchantment-link:hover {
  color: #ffffff;
  transform: translateY(2px);
  box-shadow: 0 2px 0 var(--bleu);
}
.garde .secondaires {
  margin-top: 1.4em;
}

/* Petits boutons secondaires et bouton Couverture */
.secondaires tw-link, .secondaires .enchantment-link,
.retour tw-link, .retour .enchantment-link {
  display: inline-block;
  font-size: 0.85em;
  color: var(--bleu);
  border: 2px solid var(--bleu);
  border-radius: 999px;
  padding: 0.3em 1em;
}
.secondaires tw-link:hover, .secondaires .enchantment-link:hover,
.retour tw-link:hover, .retour .enchantment-link:hover {
  background-color: var(--bleu);
  color: #ffffff;
}
.retour {
  margin: -1.2em auto 1em;
  max-width: 42em;
  text-align: right;
}

/* Le lancer de dé */
.de .consigne {
  display: block;
  font-family: "Gochi Hand", cursive;
  font-size: 1.35em;
  line-height: 1.25;
  color: var(--encre);
  margin-bottom: 0.5em;
}
.choix {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5em;
}
.choix tw-link, .choix .enchantment-link {
  display: inline-block;
  color: var(--bleu-fonce);
  background-color: #ffffff;
  border: 2px solid var(--bleu);
  border-radius: 10px;
  padding: 0.3em 0.9em;
  font-weight: 700;
}
.choix tw-link:hover, .choix .enchantment-link:hover {
  background-color: var(--bleu);
  color: #ffffff;
}
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
.separateur::before, .separateur::after {
  content: "";
  width: 3.5em;
  height: 2px;
  border-radius: 2px;
  background-color: var(--orange);
}
.separateur .lunettes {
  width: 2.6em;
  height: 1em;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 24'%3E%3Cg fill='none' stroke='%23356bac' stroke-width='3' stroke-linecap='round'%3E%3Ccircle cx='17' cy='14' r='8'/%3E%3Ccircle cx='47' cy='14' r='8'/%3E%3Cpath d='M25 13 Q32 8 39 13'/%3E%3Cpath d='M9 12 L3 6'/%3E%3Cpath d='M55 12 L61 6'/%3E%3C/g%3E%3C/svg%3E") no-repeat center / contain;
}
.garde .separateur { margin: 1em 0 0; }

/* Bouton d'élan, quand Violette entraîne le lecteur */
.elan {
  align-items: center;
  margin-top: 1.2em;
}
.elan tw-link, .elan .enchantment-link {
  font-family: "Luckiest Guy", "Impact", sans-serif;
  font-weight: 400;
  font-size: 1.45em;
  letter-spacing: 0.03em;
  color: #ffffff;
  background-color: var(--orange);
  border: none;
  border-radius: 999px;
  padding: 0.45em 1.3em 0.3em;
  box-shadow: 0 4px 0 var(--bleu);
  transform: rotate(-2deg);
}
.elan tw-link:hover, .elan .enchantment-link:hover {
  color: #ffffff;
  background-color: var(--orange);
  transform: rotate(2deg) scale(1.05);
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
  color: var(--vert);
  transform: rotate(-3deg);
}
.fin .autre-fin {
  display: block;
  font-family: "Gochi Hand", cursive;
  font-size: 1.25em;
  color: var(--gris);
  margin: 0.2em 0 0.9em;
}

/* Phrase mise en avant dans le texte */
.appel {
  font-family: "Gochi Hand", cursive;
  font-size: 1.4em;
  color: var(--orange);
}

/* Page « Comment est née cette histoire » */
.contexte h1 {
  line-height: 1.1;
  font-family: "Luckiest Guy", "Impact", sans-serif;
  font-weight: 400;
  font-size: 2em;
  color: var(--bleu);
  margin: 0 0 0.6em;
}
.contexte .credits {
  font-size: 0.92em;
  color: var(--gris);
}

/* Page de l'arbre, plus large que le texte */
.arbre {
  position: relative;
  left: 50%;
  transform: translateX(-50%);
  width: min(1100px, 94vw);
  text-align: center;
}
.arbre h1 {
  font-family: "Luckiest Guy", "Impact", sans-serif;
  font-weight: 400;
  font-size: 2.4em;
  line-height: 1.1;
  color: var(--orange);
  text-shadow: 3px 3px 0 var(--bleu);
  margin: 0;
}
.arbre .arbre-sous-titre {
  display: block;
  font-family: "Gochi Hand", cursive;
  font-size: 1.3em;
  color: var(--gris);
  margin: 0.2em 0 1em;
}
.arbre .intro-arbre {
  max-width: 40em;
  margin: 0 auto;
}
.arbre img {
  display: block;
  width: 100%;
  max-width: 900px;
  height: auto;
  margin: 1.5em auto 0.5em;
}

/* Fiches des autrices sur la page de contexte */
.visuels {
  margin-top: 2em;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1em;
}
.visuels .pleine { grid-column: 1 / -1; }
.visuels img {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 6px;
  box-shadow: 0 2px 10px rgba(43, 47, 58, 0.15);
}
.visuels img:nth-child(1) { transform: rotate(-1.5deg); }
.visuels img:nth-child(3) { transform: rotate(1.5deg); }
.legende {
  display: block;
  margin-top: 0.6em;
  font-family: "Gochi Hand", cursive;
  font-size: 1.15em;
  color: var(--gris);
  text-align: center;
}
@media (max-width: 600px) {
  .visuels { grid-template-columns: 1fr 1fr; }
}

/* Liens dans le texte */
tw-link, .enchantment-link {
  color: var(--bleu);
  font-weight: 700;
  text-decoration: none;
}
tw-link:hover, .enchantment-link:hover { color: var(--bleu-fonce); }

@media (max-width: 600px) {
  tw-story { font-size: 1.05em; }
  .garde .grand-titre { font-size: 2.9em; }
  .chapitre .titre { font-size: 1.7em; }
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


def lien(texte, cible):
    return f"[[{texte}->{cible}]]"


def passage_chapitre(ch):
    corps = []
    consigne = None
    choix = []
    suites = []
    fin = False
    appel = False
    for p in ch["paragraphes"]:
        if p.startswith("- "):
            for ligne in p.split("\n"):
                texte, cible = ligne[2:].rsplit(" -> ", 1)
                choix.append(lien(texte, f"Chapitre {cible}"))
                suites.append(texte)
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

    morceaux = ['<div class="page">',
                f'<h1 class="chapitre"><span class="numero">{ch["numero"]}</span>'
                f'<span class="titre">{ch["titre"]}</span></h1>']
    morceaux[-1] += "\n\n".join(corps)
    if not appel:
        morceaux.append(SEPARATEUR)
    if consigne:
        morceaux.append(f'<div class="de"><span class="consigne">{consigne}</span>'
                        f'<div class="choix">{"".join(choix)}</div></div>')
    elif choix:
        # Un renvoi qui n'est pas « Poursuis au chapitre… » est un élan de Violette : bouton amusant
        classe = "choix suite" if suites[0].startswith("Poursuis") else "choix suite elan"
        morceaux.append(f'<div class="{classe}">{"".join(choix)}</div>')
    if fin:
        morceaux.append('<div class="fin"><span class="mot-fin">FIN</span>'
                        '<span class="autre-fin">Il existe une autre fin à cette histoire.</span>'
                        f'<div class="secondaires">{lien("Comment est née cette histoire", "Comment est née cette histoire")}</div></div>')
    morceaux.append("</div>")
    return morceaux[0] + morceaux[1] + "".join(morceaux[2:])


def passage_garde():
    return (
        '<div class="garde"><span class="surtitre">Une histoire dont le lecteur est le héros</span>'
        f'<div class="grand-titre">{TITRE}</div>'
        f'<span class="nom-auteur">{AUTRICES}</span>{SEPARATEUR}'
        f'<div class="synopsis">{SYNOPSIS}</div>'
        f'<div class="commencer">{lien("Commencer l'histoire", "Prologue")}</div>'
        f'<div class="secondaires">{lien("Comment est née cette histoire", "Comment est née cette histoire")} '
        f'{lien("L\'arbre de l\'histoire", "L\'arbre de l\'histoire")}</div>'
        "</div>"
    )


def passage_contexte():
    return (
        '<div class="contexte">\n<h1>Comment est née cette histoire</h1>'
        + "\n\n".join(CONTEXTE)
        + f'\n\n<span class="credits">Une histoire d\'{AUTRICES}. Réalisation du livre : L.A.B, '
        "Laboratoire d'Aix-périmentation et de Bidouille.</span>\n\n"
        + f'<div class="secondaires">{lien("Commencer le livre", "Prologue")}</div>'
        + '<div class="visuels">'
        '<img src="images/fiches/fiche_recit.jpg" alt="La fiche récit remplie par Eva et Brune">'
        '<img src="images/fiches/fiche_personnage_violette.jpg" alt="La fiche personnage de Violette">'
        '<img src="images/fiches/fiche_personnage_patate.jpg" alt="La fiche personnage de Patate, avec son portrait">'
        '<img class="pleine" src="images/fiches/fiche_situation_3.jpg" alt="La fiche situation n° 3, avec ses choix au dé">'
        '</div><span class="legende">Les fiches remplies par Eva et Brune pendant l\'atelier</span>\n</div>'
    )


def passage_arbre():
    return (
        f'<div class="arbre"><h1>{TITRE}</h1>'
        f'<span class="arbre-sous-titre">Tous les chemins de l\'histoire imaginée par {AUTRICES}</span>'
        '<div class="intro-arbre">Un arbre de décision est un schéma qui montre toutes les suites possibles '
        "d'une histoire, ou d'un programme informatique. Chaque case est une étape, ici un chapitre, et chaque "
        "flèche part d'une condition : le résultat du dé, ou ce dont le lecteur se souvient. En suivant les "
        "flèches, on vérifie qu'aucun chemin ne mène nulle part : c'est grâce à cet outil que chaque parcours "
        f"de //{TITRE}// conduit bien à une fin.</div>"
        '<img src="images/arbre.svg" alt="L\'arbre de toutes les branches de l\'histoire"></div>'
    )


def construire():
    modele = SORTIE.read_text(encoding="utf-8")
    debut = modele[: modele.index("<tw-storydata")]
    moteur = modele[modele.index("</tw-storydata>"):]
    if NOINDEX not in debut:
        debut = debut.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + NOINDEX)
    debut = re.sub(r"<link rel=\"icon\"[^>]*>|<link rel=\"apple-touch-icon\"[^>]*>", "", debut)
    debut = debut.replace("<title>La Lune de Rambo</title>", f"<title>{TITRE}</title>")
    moteur = moteur.replace("JavaScript needs to be enabled to play La Lune de Rambo.",
                            f"JavaScript doit être activé pour lire {TITRE}.")
    debut = debut.replace("JavaScript needs to be enabled to play La Lune de Rambo.",
                          f"JavaScript doit être activé pour lire {TITRE}.")

    passages = [
        ("Bouton couverture", "header",
         '(unless: (passage:)\'s name is "Page de garde")[<div class="retour">[[Couverture->Page de garde]]</div>]'),
        ("Page de garde", "", passage_garde()),
        ("Comment est née cette histoire", "", passage_contexte()),
        ("L'arbre de l'histoire", "", passage_arbre()),
    ]
    for ch in lire_chapitres():
        passages.append((ch["nom"], "", passage_chapitre(ch)))

    noms = {p[0] for p in passages}
    for nom, _, contenu in passages:
        for cible in re.findall(r"->([^\]]+)\]\]", contenu):
            assert cible in noms, f"Lien cassé dans {nom} : {cible}"

    xml = [f'<tw-storydata name="{e(TITRE)}" startnode="2" creator="Twine" creator-version="2.12.1" '
           f'format="Harlowe" format-version="3.3.9" ifid="{str(uuid.uuid5(uuid.NAMESPACE_URL, TITRE)).upper()}" '
           'options="" tags="" zoom="1" hidden>',
           f'<style role="stylesheet" id="twine-user-stylesheet" type="text/twine-css">{CSS}</style>',
           '<script role="script" id="twine-user-script" type="text/twine-javascript"></script>']
    for pid, (nom, tags, contenu) in enumerate(passages, start=1):
        xml.append(f'<tw-passagedata pid="{pid}" name="{e(nom)}" tags="{tags}" '
                   f'position="{pid * 150},0" size="100,100">{e(contenu)}</tw-passagedata>')
    SORTIE.write_text(debut + "".join(xml) + moteur, encoding="utf-8")
    print(f"{SORTIE} : {len(passages)} passages")


if __name__ == "__main__":
    construire()
