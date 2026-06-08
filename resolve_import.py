# resolve_import.py

import project_manager as pm
from pathlib import Path

# ─────────────────────────────
# CONFIG
# ─────────────────────────────

BASE_DIR = Path(r"H:\Documents\Nathan\Photo")

PROJECT_NAME = "2019-04-03-Soleil"  # <- change ou automatise

project_path = None

# trouver projet
projects = pm.find_projects(BASE_DIR)
if PROJECT_NAME not in projects:
    print("Projet introuvable")
    raise SystemExit

project_path = projects[PROJECT_NAME]
import_dir = project_path / "Import"

# ─────────────────────────────
# RESOLVE CONTEXT (déjà injecté)
# ─────────────────────────────

project = resolve.GetProjectManager().GetCurrentProject()
media_pool = project.GetMediaPool()
root = media_pool.GetRootFolder()

print("Projet:", project.GetName())

# ─────────────────────────────
# ANALYSE
# ─────────────────────────────

media_files = pm.collect_media(import_dir)
orientation = pm.detect_orientation(import_dir)
resolution = pm.detect_resolution(import_dir)

print(f"Fichiers: {len(media_files)}")
print("Orientation:", orientation)
print("Résolution:", resolution)

# ─────────────────────────────
# STRUCTURE BIN
# ─────────────────────────────

rushes_bin = media_pool.AddSubFolder(root, "Rushes Auto")
media_pool.SetCurrentFolder(rushes_bin)

# ─────────────────────────────
# IMPORT MEDIA
# ─────────────────────────────

if media_files:
    imported = media_pool.ImportMedia(media_files)
    print(f"{len(imported or [])} médias importés")
else:
    print("Aucun média trouvé")

# ─────────────────────────────
# TIMELINE
# ─────────────────────────────

timeline = media_pool.CreateEmptyTimeline(f"{PROJECT_NAME}_AUTO")

if timeline:
    print("Timeline créée:", timeline.GetName())

print("Terminé")