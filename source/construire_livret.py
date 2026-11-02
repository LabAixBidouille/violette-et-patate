#!/usr/bin/env python3
"""Construit le livret imprimable de « Violette et Patate » à partir de source/texte.md.

Pages de 124 × 186 mm (format du livret de La Lune de Rambo), texte en 11 pt ; un chapitre
trop long continue sur la page suivante. Chaque renvoi indique la page du chapitre visé :
le livret est donc composé deux fois, la seconde avec les bons numéros de page.

Produit trois PDF dans le dossier Impression du livre :
- VioletteEtPatate_Livret_lecture.pdf : les pages dans l'ordre de lecture, pour relire ;
- VioletteEtPatate_Livret_A4_bord_court.pdf et _bord_long.pdf : les pages imposées deux par
  deux sur A4 paysage, avec traits de coupe, pour une impression recto verso pliée en cahier
  (choisir le fichier selon le retournement de l'imprimante).

Nécessite Google Chrome, pdftotext (poppler) et le module Python pypdf.
Usage, depuis la racine du dépôt : python3 source/construire_livret.py
"""
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from construire_site import AUTRICES, CONTEXTE, SYNOPSIS, TITRE, illustration, lire_chapitres  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent
IMPRESSION = RACINE.parent / "Impression"
NOM = "VioletteEtPatate"

MM = 72 / 25.4
LARGEUR_PAGE, HAUTEUR_PAGE = 124, 186          # mm
A4_L, A4_H = 297 * MM, 210 * MM                  # A4 paysage, en points

CSS = f"""
@font-face {{ font-family: "Luckiest Guy"; src: url("{(RACINE / 'fonts/LuckiestGuy.woff2').as_uri()}"); }}
@font-face {{ font-family: "Nunito"; font-weight: 400 800; src: url("{(RACINE / 'fonts/Nunito.woff2').as_uri()}"); }}
@font-face {{ font-family: "Nunito"; font-style: italic; src: url("{(RACINE / 'fonts/Nunito-italique.woff2').as_uri()}"); }}
@font-face {{ font-family: "Gochi Hand"; src: url("{(RACINE / 'fonts/GochiHand.woff2').as_uri()}"); }}

@page {{
  size: {LARGEUR_PAGE}mm {HAUTEUR_PAGE}mm;
  margin: 13mm 12mm 15mm 12mm;
  @bottom-center {{ content: counter(page); font-family: "Nunito"; font-size: 9pt; color: #5b6272; }}
}}
@page sans-numero {{ @bottom-center {{ content: none; }} }}

* {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; box-sizing: border-box; }}
html {{ font-family: "Nunito", sans-serif; font-size: 11pt; line-height: 1.4; color: #2b2f3a; }}
body {{ margin: 0; }}
p {{ margin: 0 0 0.6em; orphans: 2; widows: 2; }}
.page-seule {{ break-before: page; }}
.sans-numero {{ page: sans-numero; }}
.marque {{ font-size: 1pt; color: #ffffff; }}

/* Couverture */
.couverture {{ text-align: center; }}
.couverture .surtitre {{ font-family: "Gochi Hand"; font-size: 12pt; color: #5b6272; }}
.couverture .titre-livre {{ font-family: "Luckiest Guy"; font-size: 30pt; line-height: 1; color: #7b4fb0;
  text-shadow: 2.5px 2.5px 0 #ff6a00; margin: 2mm 0 1mm; }}
.couverture .autrices {{ font-family: "Gochi Hand"; font-size: 17pt; color: #ff6a00; }}
.couverture img {{ display: block; width: 100%; margin: 5mm 0; }}
.couverture .resume p {{ font-size: 11pt; }}

/* Titres */
.numero {{ display: inline-block; font-family: "Gochi Hand"; font-size: 12pt; color: #fff; background: #ff6a00;
  padding: 0.3mm 2.6mm 0.6mm; border-radius: 2mm; transform: rotate(-3deg); margin-bottom: 1.8mm; }}
h1 {{ font-family: "Luckiest Guy"; font-weight: 400; font-size: 17pt; line-height: 1.1; color: #7b4fb0;
  text-shadow: 1.5px 1.5px 0 #ff6a00; margin: 0 0 4mm; }}
.illus img {{ display: block; width: 100%; max-height: 64mm; object-fit: contain; margin: 0 auto 4mm; }}

/* Séparateur, choix, fins */
.separateur {{ text-align: center; margin: 4mm 0 3mm; break-after: avoid; }}
.separateur svg {{ width: 50mm; height: auto; }}
.appel {{ font-family: "Gochi Hand"; font-size: 14pt; color: #ff6a00; margin: 0 0 3mm; }}
/* Les choix ne restent jamais seuls en haut d'une page : ils emmènent le dernier paragraphe avec eux */
.suite {{ break-inside: avoid; break-before: avoid; }}
.consigne {{ font-family: "Gochi Hand"; font-size: 13pt; line-height: 1.25; margin: 0 0 2mm; }}
ul.choix {{ margin: 0; padding: 0; list-style: none; }}
ul.choix li {{ margin: 0 0 1.6mm; padding-left: 4mm; text-indent: -4mm; color: #7b4fb0; font-weight: 700; }}
ul.choix li::before {{ content: "•"; color: #ff6a00; display: inline-block; width: 4mm; text-indent: 0; }}
.elan {{ text-align: center; margin-top: 3mm; }}
.elan span {{ display: inline-block; font-family: "Luckiest Guy"; font-size: 11pt; letter-spacing: 0.3pt; color: #fff;
  background: #ff6a00; border-radius: 6mm; padding: 2mm 5mm 1.4mm; box-shadow: 0 1mm 0 #7b4fb0; transform: rotate(-2deg); }}
.fin {{ text-align: center; font-family: "Luckiest Guy"; font-size: 24pt; color: #3f9c80; margin-top: 2mm; }}

/* Pages de fin et de contexte */
.contexte h2 {{ font-family: "Luckiest Guy"; font-weight: 400; font-size: 15pt; color: #7b4fb0; margin: 0 0 4mm; }}
.contexte .credits {{ font-size: 9.5pt; color: #5b6272; }}
.fiches {{ display: grid; grid-template-columns: 1fr 1fr; gap: 3mm; }}
.fiches img {{ width: 100%; display: block; }}
.fiches .pleine {{ grid-column: 1 / -1; }}
.dos {{ display: flex; flex-direction: column; justify-content: flex-end; height: 156mm; text-align: center;
  font-size: 9.5pt; color: #5b6272; }}
"""

def _separateur():
    """Séparateur vectoriel : quatre boucles menthe, les lunettes violettes, quatre boucles en miroir."""
    boucles = "".join(f"M{x} 16 C{x + 8} 16 {x + 16} 14 {x + 16} 8 C{x + 16} 2 {x + 9} 2 {x + 9} 8 "
                      f"C{x + 9} 14 {x + 17} 16 {x + 26} 16 " for x in range(0, 104, 26))
    return (
        '<div class="separateur"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 288 24">'
        f'<g fill="none" stroke="#3f9c80" stroke-width="2.5" stroke-linecap="round"><path d="{boucles}"/>'
        f'<path d="{boucles}" transform="translate(288 0) scale(-1 1)"/></g>'
        '<g fill="none" stroke="#7b3fa0" stroke-width="3" stroke-linecap="round" transform="translate(112 0)">'
        '<circle cx="17" cy="14" r="8"/><circle cx="47" cy="14" r="8"/><path d="M25 13 Q32 8 39 13"/>'
        '<path d="M9 12 L3 6"/><path d="M55 12 L61 6"/></g></svg></div>'
    )


SEPARATEUR = _separateur()


def e(texte):
    return html.escape(texte, quote=False)


def italique(texte):
    return re.sub(r"//(.+?)//", r"<i>\1</i>", e(texte))


def avec_page(texte, pages):
    """Ajoute la page du dernier chapitre cité : « poursuis au chapitre 3. » → « … chapitre 3 (page 9). »"""
    m = list(re.finditer(r"chapitre (\d+)", texte))[-1]
    page = pages.get(int(m.group(1)), "00")
    return texte[: m.end()] + f" (page {page})" + texte[m.end():]


def chapitre(ch, pages):
    cle = 0 if ch["nom"] == "Prologue" else int(ch["nom"].split()[-1])
    morceaux = [f'<section class="page-seule"><span class="marque">@@CH{cle}@@</span>']
    image = RACINE / "images" / "chapitres" / f"{illustration(ch['nom'])}.jpg"
    if image.exists():
        morceaux.append(f'<div class="illus"><img src="{image.as_uri()}" alt=""></div>')
    morceaux.append(f'<span class="numero">{e(ch["numero"])}</span><h1>{e(ch["titre"])}</h1>')

    corps, consigne, choix, fin, appel = [], None, [], False, False
    for p in ch["paragraphes"]:
        if p.startswith("- "):
            for ligne in p.split("\n"):
                texte, _ = ligne[2:].rsplit(" -> ", 1)
                choix.append(texte)
        elif p == "FIN":
            fin = True
        elif p.startswith("**") and p.endswith("**"):
            interieur = p[2:-2]
            if interieur.startswith("Lance le dé") or interieur.startswith("Te souviens-tu"):
                consigne = interieur
            else:
                corps.append(f'{SEPARATEUR}<p class="appel">{e(interieur)}</p>')
                appel = True
        else:
            corps.append(f"<p>{e(p)}</p>")
    morceaux += corps

    # Le bouton du prologue n'existe que sur le site : dans le livret, on tourne simplement la page
    if ch["nom"] == "Prologue":
        choix = []
    suite = [] if appel else [SEPARATEUR]
    if consigne:
        suite.append(f'<p class="consigne">{e(consigne)}</p><ul class="choix">'
                     + "".join(f"<li>{e(avec_page(c, pages))}</li>" for c in choix) + "</ul>")
    elif choix:
        suite.append(f'<div class="elan"><span>{e(avec_page(choix[0], pages))}</span></div>')
    if fin:
        suite.append('<div class="fin">FIN</div>')
    if consigne or choix or fin:
        morceaux.append(f'<div class="suite">{"".join(suite)}</div>')
    morceaux.append("</section>")
    return "".join(morceaux)


def document(pages, blanches=0):
    couverture = (
        '<section class="couverture sans-numero">'
        '<div class="surtitre">Une histoire dont le lecteur est le héros</div>'
        f'<div class="titre-livre">{e(TITRE)}</div><div class="autrices">{e(AUTRICES)}</div>'
        f'<img src="{(RACINE / "images/couverture.jpg").as_uri()}" alt="">'
        '<div class="resume">' + "".join(f"<p>{e(p)}</p>" for p in SYNOPSIS.split("\n\n")) + "</div></section>"
    )
    fiches = RACINE / "images" / "fiches"
    contexte = (
        '<section class="page-seule contexte"><h2>Comment est née cette histoire</h2>'
        + "".join(f"<p>{italique(p)}</p>" for p in CONTEXTE)
        + f'<p class="credits">Une histoire d\'{e(AUTRICES)}. Réalisation du livre : L.A.B, '
          "Laboratoire d'Aix-périmentation et de Bidouille.</p></section>"
        '<section class="page-seule contexte"><h2>Les fiches d\'Eva et Brune</h2><div class="fiches">'
        f'<img src="{(fiches / "fiche_recit.jpg").as_uri()}" alt="">'
        f'<img src="{(fiches / "fiche_personnage_violette.jpg").as_uri()}" alt="">'
        f'<img class="pleine" src="{(fiches / "fiche_situation_4.jpg").as_uri()}" alt="">'
        "</div></section>"
    )
    chapitres = "".join(chapitre(ch, pages) for ch in lire_chapitres())
    vides = '<section class="page-seule sans-numero">&nbsp;</section>' * blanches
    dos = ('<section class="page-seule sans-numero"><div class="dos">'
           f"<p><b>{e(TITRE)}</b>, une histoire d'{e(AUTRICES)}, imaginée pendant l'atelier "
           "« Le livre dont tu es le héros » à la bibliothèque des Deux Ormes, Aix-en-Provence, "
           "en octobre 2026.</p><p>Réalisation du livre : L.A.B, Laboratoire d'Aix-périmentation et de Bidouille.</p>"
           "</div></section>")
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f"<body>{couverture}{contexte}{chapitres}{vides}{dos}</body></html>")


def imprimer(source_html, pdf):
    subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=8000", f"--print-to-pdf={pdf}", source_html.as_uri()],
                   check=True, capture_output=True)


def reperer_pages(pdf):
    """Numéro de page où commence chaque chapitre (0 pour le prologue), d'après les marques invisibles."""
    pages = {}
    total = len(PdfReader(str(pdf)).pages)
    for n in range(1, total + 1):
        texte = subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), str(pdf), "-"],
                               capture_output=True, text=True, check=True).stdout
        for cle in re.findall(r"@@CH(\d+)@@", texte):
            pages[int(cle)] = n
    return pages, total


def composer(dossier):
    source = Path(dossier) / "livret.html"
    pdf = Path(dossier) / "livret.pdf"
    pages = {}
    for _ in range(4):
        source.write_text(document(pages), encoding="utf-8")
        imprimer(source, pdf)
        nouvelles, total = reperer_pages(pdf)
        if nouvelles == pages:
            break
        pages = nouvelles
    else:
        raise SystemExit("Les numéros de page ne se stabilisent pas.")
    # Pages blanches avant le dos pour arriver à un multiple de 4 (cahier plié)
    blanches = (-total) % 4
    if blanches:
        source.write_text(document(pages, blanches), encoding="utf-8")
        imprimer(source, pdf)
        assert reperer_pages(pdf)[0] == pages
    return pdf, pages


def traits_de_coupe(dossier):
    """Page A4 paysage avec les traits de coupe des deux pages du livret côte à côte."""
    x0 = (297 - 2 * LARGEUR_PAGE) / 2
    y0 = (210 - HAUTEUR_PAGE) / 2
    traits = []
    for x in (x0, x0 + LARGEUR_PAGE, x0 + 2 * LARGEUR_PAGE):
        for y, sens in ((y0, -1), (y0 + HAUTEUR_PAGE, 1)):
            y1, y2 = (y - 2 - 5, y - 2) if sens < 0 else (y + 2, y + 2 + 5)
            traits.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}"/>')
    for y in (y0, y0 + HAUTEUR_PAGE):
        for x, sens in ((x0, -1), (x0 + 2 * LARGEUR_PAGE, 1)):
            x1, x2 = (x - 2 - 5, x - 2) if sens < 0 else (x + 2, x + 2 + 5)
            traits.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}"/>')
    source = Path(dossier) / "traits.html"
    source.write_text(
        '<!doctype html><html><head><style>@page { size: 297mm 210mm; margin: 0; } body { margin: 0; }</style></head>'
        '<body><svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">'
        f'<g stroke="#000" stroke-width="0.15">{"".join(traits)}</g></svg></body></html>', encoding="utf-8")
    pdf = Path(dossier) / "traits.pdf"
    imprimer(source, pdf)
    return PdfReader(str(pdf)).pages[0]


def imposer(lecture, traits, sortie, bord_long):
    pages = PdfReader(str(lecture)).pages
    n = len(pages)
    assert n % 4 == 0
    x0 = (A4_L - 2 * LARGEUR_PAGE * MM) / 2
    y0 = (A4_H - HAUTEUR_PAGE * MM) / 2
    ecrivain = PdfWriter()

    def face(gauche, droite, retournee):
        feuille = PageObject.create_blank_page(width=A4_L, height=A4_H)
        feuille.merge_page(traits)
        for indice, x in ((gauche, x0), (droite, x0 + LARGEUR_PAGE * MM)):
            feuille.merge_transformed_page(pages[indice - 1], Transformation().translate(x, y0))
        if retournee:
            feuille.rotate(180)
        ecrivain.add_page(feuille)

    for i in range(n // 4):
        face(n - 2 * i, 1 + 2 * i, False)          # recto : dernière page à gauche, première à droite
        face(2 + 2 * i, n - 1 - 2 * i, bord_long)  # verso
    with open(sortie, "wb") as f:
        ecrivain.write(f)


def construire():
    IMPRESSION.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as dossier:
        pdf, pages = composer(dossier)
        lecture = IMPRESSION / f"{NOM}_Livret_lecture.pdf"
        lecture.write_bytes(pdf.read_bytes())
        traits = traits_de_coupe(dossier)
        imposer(lecture, traits, IMPRESSION / f"{NOM}_Livret_A4_bord_court.pdf", bord_long=False)
        imposer(lecture, traits, IMPRESSION / f"{NOM}_Livret_A4_bord_long.pdf", bord_long=True)
    total = len(PdfReader(str(lecture)).pages)
    print(f"{lecture} : {total} pages, soit {total // 4} feuilles A4 recto verso")
    print("Pages des chapitres :", ", ".join(f"{'P' if k == 0 else k}→{v}" for k, v in sorted(pages.items())))


if __name__ == "__main__":
    construire()
