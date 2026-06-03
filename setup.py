import os
import sys
import shutil
from datetime import datetime
from collections import defaultdict

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    print("Installation de Pillow...")
    os.system(f"{sys.executable} -m pip install Pillow")
    from PIL import Image
    from PIL.ExifTags import TAGS

# ── Config ──────────────────────────────────────────────
SOURCE_DIR = "_A_retouche"
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".cr2", ".nef", ".arw", ".dng"}
SUB_DIRS = ["Export", "Import", "ResolveProject"]
# ────────────────────────────────────────────────────────

def get_exif_date(filepath):
    """Extrait la date de prise de vue depuis les métadonnées EXIF."""
    try:
        img = Image.open(filepath)
        exif_data = img._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "DateTimeOriginal":
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    # Fallback : date de modification du fichier
    timestamp = os.path.getmtime(filepath)
    return datetime.fromtimestamp(timestamp)

def get_photos(directory):
    """Retourne toutes les photos du dossier source."""
    photos = []
    for f in sorted(os.listdir(directory)):
        if os.path.splitext(f)[1].lower() in PHOTO_EXTENSIONS:
            photos.append(os.path.join(directory, f))
    return photos

def group_by_date(photos):
    """Groupe les photos par date (YYYY-MM-DD)."""
    groups = defaultdict(list)
    for photo in photos:
        date = get_exif_date(photo)
        key = date.strftime("%Y-%m-%d")
        groups[key].append(photo)
    return dict(sorted(groups.items()))

def merge_isolated_dates(groups):
    """Fusionne les dates avec une seule photo avec le groupe de date le plus proche."""
    if len(groups) <= 3:
        return groups

    merged = {d: list(photos) for d, photos in groups.items()}

    changed = True
    while changed:
        changed = False
        dates = sorted(merged.keys())
        for date_str in dates:
            if len(merged[date_str]) == 1:
                current = datetime.strptime(date_str, "%Y-%m-%d")
                other_dates = [d for d in merged if d != date_str]
                if not other_dates:
                    break
                closest = min(
                    other_dates,
                    key=lambda d: abs((datetime.strptime(d, "%Y-%m-%d") - current).days)
                )
                print(f"  🔀 Photo isolée du {date_str} fusionnée avec le groupe du {closest}")
                merged[closest].extend(merged[date_str])
                del merged[date_str]
                changed = True
                break  # redémarre après chaque modification

    return dict(sorted(merged.items()))

def create_project(base_dir, date_str, project_name, photos):
    """Crée la structure de dossiers et déplace les photos."""
    year = date_str[:4]
    folder_name = f"{date_str}-{project_name}"
    year_dir = os.path.join(base_dir, year)
    project_dir = os.path.join(year_dir, folder_name)

    # Créer dossier année
    os.makedirs(year_dir, exist_ok=True)

    # Vérifier si le projet existe déjà
    if os.path.exists(project_dir):
        print(f"  ⚠️  Le dossier '{folder_name}' existe déjà, photos ajoutées à Import.")
    else:
        os.makedirs(project_dir)
        for sub in SUB_DIRS:
            os.makedirs(os.path.join(project_dir, sub))
        print(f"  ✅ Projet créé : {project_dir}")

    # Déplacer les photos dans Import
    import_dir = os.path.join(project_dir, "Import")
    moved = 0
    for photo in photos:
        dest = os.path.join(import_dir, os.path.basename(photo))
        if not os.path.exists(dest):
            shutil.move(photo, dest)
            moved += 1
        else:
            print(f"  ⚠️  Fichier déjà présent, ignoré : {os.path.basename(photo)}")
    print(f"  📁 {moved} photo(s) déplacée(s) dans Import\n")

def main():
    # Vérification du dossier source
    if not os.path.isdir(SOURCE_DIR):
        print(f"❌ Dossier source introuvable : '{SOURCE_DIR}'")
        print("   Place ce script à côté du dossier '_A_retouche' et relance.")
        sys.exit(1)

    photos = get_photos(SOURCE_DIR)
    if not photos:
        print(f"Aucune photo trouvée dans '{SOURCE_DIR}'.")
        sys.exit(0)

    groups = group_by_date(photos)
    groups = merge_isolated_dates(groups)

    print(f"\n📷 {len(photos)} photo(s) trouvée(s), regroupées en {len(groups)} date(s).\n")
    print("─" * 50)

    base_dir = os.path.dirname(os.path.abspath(SOURCE_DIR))

    for date_str, date_photos in groups.items():
        print(f"📅 Date : {date_str}  ({len(date_photos)} photo(s))")
        print(f"   Aperçu : {[os.path.basename(p) for p in date_photos[:3]]}"
              + (" ..." if len(date_photos) > 3 else ""))

        while True:
            project_name = input(f"   Nom du projet pour le {date_str} : ").strip()
            if project_name:
                break
            print("   ⚠️  Le nom ne peut pas être vide.")

        create_project(base_dir, date_str, project_name, date_photos)

    print("─" * 50)
    print("✅ Tous les projets ont été créés !")

if __name__ == "__main__":
    main()