#!/usr/bin/env python3
"""Dessine images/arbre.svg, l'arbre de toutes les branches de l'histoire.

La position des cases et le tracé des flèches sont fixés à la main ci-dessous. Les titres
viennent de source/texte.md, et le script vérifie que les flèches dessinées correspondent
exactement aux renvois du texte : si le texte change, il s'arrête au lieu de dessiner un
arbre faux.

Usage, depuis la racine du dépôt : python3 source/construire_arbre.py
"""
import base64
import html
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
TEXTE = RACINE / "source" / "texte.md"
SORTIE = RACINE / "images" / "arbre.svg"
POLICE = RACINE / "fonts" / "Nunito.woff2"

# Couleurs des illustrations du livre
CORAIL, JAUNE_CLAIR, VIOLET, MENTHE, ENCRE = "#e0442f", "#fff4cc", "#7b4fb0", "#3f9c80", "#2b2f3a"
# Cadre resserré sur le dessin, de la boucle de gauche à la case 6
GAUCHE, LARGEUR, HAUTEUR = 85, 1040, 2720
L_CASE, H_CASE = 230, 66

# Centre horizontal et haut de chaque case
CASES = {
    "P": (560, 60), 1: (560, 190), 2: (560, 320),
    3: (260, 480), 4: (860, 480), 5: (740, 640), 6: (1000, 640),
    7: (560, 800), 8: (260, 960), 9: (260, 1120), 10: (560, 1290),
    11: (300, 1450), 12: (820, 1450), 13: (560, 1610), 14: (260, 1770),
    15: (560, 1930), 16: (560, 2090), 17: (260, 2250), 18: (560, 2410),
    19: (300, 2570), 20: (820, 2570),
}
FINS = {19, 20}
# Icône sous la case : dé, ou point d'interrogation quand le lecteur doit se souvenir
ICONES = {2: "de", 4: "de", 7: "de", 8: "de", 9: "de", 10: "de", 13: "de", 14: "de", 16: "de", 18: "question"}

# (départ, arrivée, tracé, étiquettes [(texte, x, y)])
FLECHES = [
    ("P", 1, [(560, 126), (560, 190)], []),
    (1, 2, [(560, 256), (560, 320)], []),
    (2, 3, [(560, 430), (260, 430), (260, 480)], [("pair", 410, 430)]),
    (2, 4, [(560, 430), (860, 430), (860, 480)], [("impair", 710, 430)]),
    (3, 7, [(260, 546), (260, 770), (530, 770), (530, 800)], []),
    (4, 5, [(860, 590), (740, 590), (740, 640)], [("pair", 790, 590)]),
    (4, 6, [(860, 590), (1000, 590), (1000, 640)], [("impair", 940, 590)]),
    (5, 7, [(740, 706), (740, 770), (560, 770), (560, 800)], []),
    (6, 7, [(1000, 706), (1000, 785), (590, 785), (590, 800)], []),
    (7, 8, [(560, 910), (260, 910), (260, 960)], [("pair", 410, 910)]),
    (7, 10, [(560, 910), (560, 1290)], [("impair", 560, 1000)]),
    (8, 9, [(260, 1070), (260, 1120)], [("1, 3 ou 5", 260, 1093)]),
    (8, 10, [(260, 1070), (510, 1070), (510, 1290)], [("2, 4 ou 6", 385, 1070)]),
    (9, 9, [(260, 1230), (100, 1230), (100, 1153), (145, 1153)], [("1, 3 ou 5", 180, 1230)]),
    (9, 10, [(260, 1230), (260, 1323), (445, 1323)], [("2, 4 ou 6", 260, 1268), ("après deux relectures", 352, 1323)]),
    (10, 11, [(560, 1400), (300, 1400), (300, 1450)], [("pair", 430, 1400)]),
    (10, 12, [(560, 1400), (820, 1400), (820, 1450)], [("impair", 690, 1400)]),
    (11, 13, [(300, 1516), (300, 1580), (530, 1580), (530, 1610)], []),
    (12, 13, [(820, 1516), (820, 1580), (590, 1580), (590, 1610)], []),
    (13, 14, [(560, 1720), (260, 1720), (260, 1770)], [("impair", 410, 1720)]),
    (13, 15, [(560, 1720), (560, 1930)], [("pair", 560, 1820)]),
    (14, 14, [(260, 1880), (100, 1880), (100, 1803), (145, 1803)], [("impair", 180, 1880)]),
    (14, 15, [(260, 1880), (260, 1963), (445, 1963)], [("pair", 260, 1918), ("après deux relectures", 352, 1963)]),
    (15, 16, [(560, 1996), (560, 2090)], []),
    (16, 17, [(560, 2200), (260, 2200), (260, 2250)], [("impair", 410, 2200)]),
    (16, 18, [(560, 2200), (560, 2410)], [("pair", 560, 2300)]),
    (17, 18, [(260, 2316), (260, 2443), (445, 2443)], []),
    (18, 19, [(560, 2520), (300, 2520), (300, 2570)], [("Mirette rencontrée", 430, 2520)]),
    (18, 20, [(560, 2520), (820, 2520), (820, 2570)], [("sinon", 690, 2520)]),
]


def lire_texte():
    titres, renvois = {}, set()
    actuel = None
    for ligne in TEXTE.read_text(encoding="utf-8").split("\n"):
        m = re.match(r"## (Prologue|Chapitre (\d+))\. (.+)", ligne)
        if m:
            actuel = "P" if m.group(1) == "Prologue" else int(m.group(2))
            titres[actuel] = m.group(3)
        m = re.match(r"- .+ -> (\d+)$", ligne)
        if m:
            renvois.add((actuel, int(m.group(1))))
    return titres, renvois


def couper(texte, largeur=23):
    lignes, ligne = [], ""
    for mot in texte.split():
        if ligne and len(ligne) + 1 + len(mot) > largeur:
            lignes.append(ligne)
            ligne = mot
        else:
            ligne = f"{ligne} {mot}".strip()
    return lignes + [ligne]


def case(cle, titre):
    cx, haut = CASES[cle]
    x = cx - L_CASE / 2
    contour = MENTHE if cle in FINS else VIOLET
    svg = [f'<rect x="{x}" y="{haut}" width="{L_CASE}" height="{H_CASE}" rx="12" fill="#fff" stroke="{contour}" stroke-width="2.5"/>']
    lignes = couper(titre)
    if len(lignes) > 2:
        lignes = couper(titre, 27)
    taille, interligne = (17, 18) if len(lignes) < 3 else (14.5, 15.5)
    y0 = haut + H_CASE / 2 - (len(lignes) - 1) * interligne / 2 + 6
    for i, l in enumerate(lignes):
        svg.append(f'<text x="{cx}" y="{y0 + i * interligne}" font-size="{taille}" text-anchor="middle" fill="{ENCRE}">{html.escape(l)}</text>')
    etiquette = "Prologue" if cle == "P" else str(cle)
    lb = 76 if cle == "P" else (30 if cle < 10 else 36)
    svg.append(f'<rect x="{x + 8}" y="{haut - 11}" width="{lb}" height="22" rx="11" fill="{CORAIL}"/>')
    svg.append(f'<text x="{x + 8 + lb / 2}" y="{haut + 5}" font-size="14" font-weight="800" text-anchor="middle" fill="#fff">{etiquette}</text>')
    if cle in FINS:
        svg.append(f'<text x="{cx}" y="{haut + H_CASE + 34}" font-size="24" font-weight="800" text-anchor="middle" fill="{MENTHE}">FIN</text>')
    return "\n".join(svg)


def icone(cle):
    cx, haut = CASES[cle]
    y = haut + H_CASE + 8
    svg = [f'<line x1="{cx}" y1="{haut + H_CASE}" x2="{cx}" y2="{y}" stroke="{VIOLET}" stroke-width="2"/>',
           f'<rect x="{cx - 13}" y="{y}" width="26" height="26" rx="6" fill="{JAUNE_CLAIR}" stroke="{CORAIL}" stroke-width="2"/>']
    if ICONES[cle] == "de":
        for dx, dy in ((-6, -6), (0, 0), (6, 6)):
            svg.append(f'<circle cx="{cx + dx}" cy="{y + 13 + dy}" r="2.6" fill="{CORAIL}"/>')
    else:
        svg.append(f'<text x="{cx}" y="{y + 19}" font-size="17" font-weight="800" text-anchor="middle" fill="{CORAIL}">?</text>')
    svg.append(f'<line x1="{cx}" y1="{y + 26}" x2="{cx}" y2="{y + 36}" stroke="{VIOLET}" stroke-width="2"/>')
    return "\n".join(svg)


def fleche(points, etiquettes):
    trace = " ".join(f"{x},{y}" for x, y in points)
    svg = [f'<polyline points="{trace}" fill="none" stroke="{VIOLET}" stroke-width="2" marker-end="url(#pointe)"/>']
    for texte, x, y in etiquettes:
        largeur = 8.2 * len(texte) + 18
        svg.append(f'<rect x="{x - largeur / 2}" y="{y - 11}" width="{largeur}" height="22" rx="11" fill="#fff" stroke="{VIOLET}" stroke-width="1.5"/>')
        svg.append(f'<text x="{x}" y="{y + 5}" font-size="15" text-anchor="middle" fill="{VIOLET}">{html.escape(texte)}</text>')
    return "\n".join(svg)


def construire():
    titres, renvois = lire_texte()
    dessinees = {(a, b) for a, b, _, _ in FLECHES}
    assert set(titres) == set(CASES), f"Chapitres du texte et cases de l'arbre différents : {set(titres) ^ set(CASES)}"
    assert renvois == dessinees, f"Renvois du texte et flèches de l'arbre différents : {renvois ^ dessinees}"

    police = base64.b64encode(POLICE.read_bytes()).decode()
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{GAUCHE} 0 {LARGEUR} {HAUTEUR}" width="{LARGEUR}" height="{HAUTEUR}" font-family="Nunito, sans-serif">',
           f'<defs><style>@font-face{{font-family:"Nunito";font-weight:400 800;src:url(data:font/woff2;base64,{police}) format("woff2");}}</style>',
           f'<marker id="pointe" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{VIOLET}"/></marker></defs>']
    svg += [fleche(t, e) for _, _, t, e in FLECHES]
    svg += [icone(c) for c in ICONES]
    svg += [case(c, titres[c]) for c in CASES]
    svg.append("</svg>")
    SORTIE.parent.mkdir(exist_ok=True)
    SORTIE.write_text("\n".join(svg), encoding="utf-8")
    print(f"{SORTIE} : {len(CASES)} cases, {len(FLECHES)} flèches")


if __name__ == "__main__":
    construire()
