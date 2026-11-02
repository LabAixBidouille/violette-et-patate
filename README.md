# Violette et Patate

Une histoire dont le lecteur est le héros, imaginée par Eva et Brune pendant l'atelier « Le livre dont tu es le héros » du L.A.B, à la bibliothèque des Deux Ormes (bibliothèques Méjanes, Aix-en-Provence), le 27 octobre 2026.

Le site est en ligne sur https://labaixbidouille.github.io/violette-et-patate/. Il n'est pas référencé par les moteurs de recherche.

## Modifier le livre

Le texte se trouve dans `source/texte.md`. Chaque chapitre commence par `## Chapitre n. Titre`, les choix s'écrivent `- texte du lien -> n` et une fin se termine par `FIN`. La couverture, la page « Comment est née cette histoire » et la mise en forme sont dans `source/construire_site.py`. Les illustrations sont dans `images/chapitres/` (`prologue.jpg`, `chapitre-01.jpg`…, en 1200 pixels de large au plus) et la couverture dans `images/couverture.jpg` ; une page sans image s'affiche sur une seule colonne. L'arbre se redessine avec `python3 source/construire_arbre.py`.

Après une modification, reconstruire la page puis publier :

```
python3 source/construire_site.py
```

Réalisation du livre : L.A.B, Laboratoire d'Aix-périmentation et de Bidouille.

## Livret imprimé

`python3 source/construire_livret.py` compose le livret (pages de 124 × 186 mm, texte en 11 pt, renvois avec numéros de page) et l'imposition sur A4 paysage pour un cahier agrafé. Les PDF sont écrits dans le dossier `Impression` du livre, hors du dépôt. Il faut Google Chrome, `pdftotext` (poppler-utils) et le module Python `pypdf`.

