# 📷 Photo Workflow Manager

Deux scripts Python pour organiser et suivre ta pipeline de retouche photo, de l'import jusqu'à l'export DaVinci Resolve.

---

## Vue d'ensemble

Ce projet automatise deux tâches répétitives :

1. **Organiser** les photos brutes en projets structurés, regroupées par date de prise de vue
2. **Suivre** l'avancement des retouches à travers les différentes étapes du workflow

---

## Structure des dossiers générée

```
repo/
├── 2024/
│   ├── 2024-06-14-Mariage-Dupont/
│   │   ├── Import/          ← photos brutes déplacées ici
│   │   ├── Export/          ← exports finaux
│   │   └── ResolveProject/  ← fichiers .drp DaVinci Resolve
│   └── 2024-08-03-Portrait/
│       └── ...
├── 2025/
│   └── ...
├── _A_retouche/             ← dossier de dépôt des nouvelles photos
├── generate_changelog.py
├── organisateur_photos.py
├── CHANGELOG.md
└── hooks/
    ├── pre-commit
    └── install_hooks.sh
```

---

## Scripts

### `organisateur_photos.py` — Import & organisation

Scanne le dossier `_A_retouche/`, lit les métadonnées EXIF de chaque photo pour extraire la date de prise de vue, regroupe les photos par jour, puis crée la structure de projet et déplace les fichiers.

**Comportement intelligent :**
- Les photos isolées (seule photo d'une journée) sont automatiquement fusionnées avec le groupe de date le plus proche
- Fallback sur la date de modification du fichier si les EXIF sont absents
- Ne réécrase jamais un fichier déjà présent dans `Import/`

**Lancement :**
```bash
python organisateur_photos.py
```

Le script est interactif : pour chaque groupe de dates détecté, il demande un nom de projet.

```
📷 6 photo(s) trouvée(s), regroupées en 2 date(s).

📅 Date : 2024-06-14  (5 photo(s))
   Aperçu : ['IMG_001.jpg', 'IMG_002.jpg', 'IMG_003.jpg'] ...
   Nom du projet pour le 2024-06-14 : Mariage-Dupont

  ✅ Projet créé : /Users/toi/Photos/2024/2024-06-14-Mariage-Dupont
  📁 5 photo(s) déplacée(s) dans Import
```

**Formats supportés :** `.jpg` `.jpeg` `.png` `.tiff` `.tif` `.cr2` `.nef` `.arw` `.dng`

---

### `generate_changelog.py` — Suivi de l'avancement

Parcourt tous les dossiers années et projets pour évaluer l'état de chaque retouche, puis génère (ou met à jour) `CHANGELOG.md`.

**Un projet est considéré terminé quand :**
- ✅ Un fichier `.drp` est présent dans `ResolveProject/` **ET**
- ✅ Au moins un fichier est présent dans `Export/`

| Icône | Statut |
|-------|--------|
| ✅ | Terminé |
| 🔧 | En cours — projet Resolve créé, export manquant |
| ⏳ | À faire — pas encore ouvert dans Resolve |

**Lancement :**
```bash
python generate_changelog.py
```

Chaque exécution **ajoute un nouveau snapshot** en haut du `CHANGELOG.md` sans effacer l'historique, ce qui permet de voir l'avancement dans le temps.

---

## Installation

### Prérequis

- Python 3.8+
- [Pillow](https://pillow.readthedocs.io/) (installé automatiquement au premier lancement si absent)

### Mise en place

```bash
# 1. Cloner le repo
git clone <url-du-repo>
cd <nom-du-repo>

# 2. Installer les git hooks (une seule fois)
sh hooks/install_hooks.sh
```

C'est tout. Le changelog se mettra à jour automatiquement à chaque `git commit`.

---

## Git hooks

Le dossier `hooks/` contient un hook `pre-commit` versionné qui lance `generate_changelog.py` automatiquement avant chaque commit et ajoute le `CHANGELOG.md` mis à jour au commit.

Pour l'activer après un clone :
```bash
sh hooks/install_hooks.sh
```

> Si tu travailles à plusieurs sur le repo, chaque collaborateur doit lancer cette commande une fois après le clone.

---

## Workflow typique

```
1. Copier les photos brutes dans _A_retouche/
          ↓
2. python organisateur_photos.py
   → Nommer les projets
   → Les photos sont rangées dans Import/
          ↓
3. Ouvrir DaVinci Resolve
   → Créer/enregistrer le projet dans ResolveProject/
   → Exporter les fichiers finaux dans Export/
          ↓
4. git commit
   → CHANGELOG.md mis à jour automatiquement
```

---

## Dépendances

| Package | Usage | Installation |
|---------|-------|-------------|
| `Pillow` | Lecture des métadonnées EXIF | Auto au premier lancement, ou `pip install Pillow` |
