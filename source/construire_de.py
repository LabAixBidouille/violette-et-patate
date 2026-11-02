#!/usr/bin/env python3
"""Dessine le dé à fabriquer de « Violette et Patate » sur une page A5, dans un PDF à part.

Patron de cube en croix, faces de 29 mm : deux faces opposées font toujours 7. Les traits pleins
se découpent, les pointillés se plient, les languettes lavande se collent.

Produit Impression/VioletteEtPatate_De.pdf. Nécessite Google Chrome.
Usage, depuis la racine du dépôt : python3 source/construire_de.py
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from construire_livret import CSS as CSS_LIVRET, SEPARATEUR, imprimer  # noqa: E402
from construire_site import AUTRICES, TITRE  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE.parent / "Impression" / "VioletteEtPatate_De.pdf"

FACE = 29          # côté d'une face, en mm
LANGUETTE = 7      # profondeur des languettes, en mm
VIOLET, ORANGE, MENTHE, LAVANDE = "#7b4fb0", "#ff6a00", "#3f9c80", "#efe7f8"

# Position (colonne, ligne) de chaque face dans la croix et sa valeur : A en haut, puis B, C, D
# dans la colonne du milieu, L et R de part et d'autre de B. Opposées : A–C, B–D, L–R.
FACES = {"A": ((1, 0), 2), "L": ((0, 1), 3), "B": ((1, 1), 1), "R": ((2, 1), 4),
         "C": ((1, 2), 5), "D": ((1, 3), 6)}

# Points de chaque valeur, en fractions de la face
POINTS = {
    1: [(0.5, 0.5)],
    2: [(0.27, 0.27), (0.73, 0.73)],
    3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
    4: [(0.27, 0.27), (0.73, 0.27), (0.27, 0.73), (0.73, 0.73)],
    5: [(0.25, 0.25), (0.75, 0.25), (0.5, 0.5), (0.25, 0.75), (0.75, 0.75)],
    6: [(0.28, 0.22), (0.72, 0.22), (0.28, 0.5), (0.72, 0.5), (0.28, 0.78), (0.72, 0.78)],
}

# Languettes : (face, côté). Sept collages pour fermer le cube.
LANGUETTES = [("A", "haut"), ("L", "haut"), ("L", "gauche"), ("L", "bas"),
              ("R", "haut"), ("R", "droite"), ("R", "bas")]


def languette(x, y, cote):
    """Trapèze collé au bord d'une face dont le coin haut gauche est (x, y)."""
    f, l, r = FACE, LANGUETTE, LANGUETTE * 0.9
    points = {
        "haut": [(x, y), (x + r, y - l), (x + f - r, y - l), (x + f, y)],
        "bas": [(x, y + f), (x + r, y + f + l), (x + f - r, y + f + l), (x + f, y + f)],
        "gauche": [(x, y), (x - l, y + r), (x - l, y + f - r), (x, y + f)],
        "droite": [(x + f, y), (x + f + l, y + r), (x + f + l, y + f - r), (x + f, y + f)],
    }[cote]
    trace = " ".join(f"{px:.2f},{py:.2f}" for px, py in points)
    return f'<polygon points="{trace}" fill="{LAVANDE}" stroke="{VIOLET}" stroke-width="0.35"/>'


def patron():
    ox, oy = LANGUETTE, LANGUETTE
    largeur, hauteur = 3 * FACE + 2 * LANGUETTE, 4 * FACE + 2 * LANGUETTE
    dessin = []
    for nom, cote in LANGUETTES:
        (c, li), _ = FACES[nom]
        dessin.append(languette(ox + c * FACE, oy + li * FACE, cote))
    for (c, li), valeur in FACES.values():
        x, y = ox + c * FACE, oy + li * FACE
        dessin.append(f'<rect x="{x}" y="{y}" width="{FACE}" height="{FACE}" fill="#fff"/>')
        for px, py in POINTS[valeur]:
            dessin.append(f'<circle cx="{x + px * FACE:.2f}" cy="{y + py * FACE:.2f}" r="2.8" fill="{ORANGE}"/>')
    # Contour découpé en trait plein, puis pliures en pointillés par-dessus
    contour = [(1, 0), (2, 0), (2, 1), (3, 1), (3, 2), (2, 2), (2, 4), (1, 4), (1, 2), (0, 2), (0, 1), (1, 1)]
    trace = " ".join(f"{ox + c * FACE},{oy + li * FACE}" for c, li in contour)
    dessin.append(f'<polygon points="{trace}" fill="none" stroke="{VIOLET}" stroke-width="0.6"/>')
    plis = [((1, 1), (2, 1)), ((1, 2), (2, 2)), ((1, 3), (2, 3)),    # sous A, sous B, sous C
            ((1, 1), (1, 2)), ((2, 1), (2, 2))]                        # de part et d'autre de B
    for (x1, y1), (x2, y2) in plis:
        dessin.append(f'<line x1="{ox + x1 * FACE}" y1="{oy + y1 * FACE}" x2="{ox + x2 * FACE}" '
                      f'y2="{oy + y2 * FACE}" stroke="{MENTHE}" stroke-width="0.45" stroke-dasharray="1.6 1.2"/>')
    for nom, cote in LANGUETTES:   # pli à la base de chaque languette
        (c, li), _ = FACES[nom]
        x, y = ox + c * FACE, oy + li * FACE
        bord = {"haut": (x, y, x + FACE, y), "bas": (x, y + FACE, x + FACE, y + FACE),
                "gauche": (x, y, x, y + FACE), "droite": (x + FACE, y, x + FACE, y + FACE)}[cote]
        dessin.append(f'<line x1="{bord[0]}" y1="{bord[1]}" x2="{bord[2]}" y2="{bord[3]}" '
                      f'stroke="{MENTHE}" stroke-width="0.45" stroke-dasharray="1.6 1.2"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{largeur}mm" height="{hauteur}mm" '
            f'viewBox="0 0 {largeur} {hauteur}">{"".join(dessin)}</svg>')


def construire():
    css = CSS_LIVRET.split("@page {")[0] + """
@page { size: 148mm 210mm; margin: 12mm; }
* { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
html { font-family: "Nunito", sans-serif; font-size: 11pt; line-height: 1.4; color: #2b2f3a; }
body { margin: 0; text-align: center; }
h1 { font-family: "Luckiest Guy"; font-weight: 400; font-size: 22pt; color: #7b4fb0;
  text-shadow: 1.5px 1.5px 0 #ff6a00; margin: 0; }
.consigne { margin: 0 auto 3mm; max-width: 112mm; }
.separateur { margin: 2mm 0 3mm; }
.separateur svg { width: 46mm; height: auto; }
.patron { display: flex; justify-content: center; }
.signature { font-family: "Gochi Hand"; font-size: 11pt; color: #5b6272; margin-top: 2mm; }
"""
    page = (
        f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>{css}</style></head><body>'
        f"<h1>Ton dé à fabriquer</h1>{SEPARATEUR}"
        '<p class="consigne">Découpe le long des traits pleins, plie le long des pointillés, puis colle '
        "les languettes à l'intérieur. Sur un dé, deux faces opposées font toujours 7.</p>"
        f'<div class="patron">{patron()}</div>'
        f'<p class="signature">{TITRE}, une histoire d\'{AUTRICES}</p></body></html>'
    )
    SORTIE.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as dossier:
        source = Path(dossier) / "de.html"
        source.write_text(page, encoding="utf-8")
        imprimer(source, SORTIE)
    print(SORTIE)


if __name__ == "__main__":
    construire()
