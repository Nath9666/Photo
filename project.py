"""
project.py — Création automatique d'un projet DaVinci Resolve
=============================================================
Deux modes d'utilisation :

  MODE 1 — API DaVinci (Resolve ouvert)
    Import des clips depuis le dossier Import/ du projet.

  MODE 2 — Clonage de template (Resolve fermé)
    Copie TemplatePortrait.drp ou TemplatesPaysage.drp dans ResolveProject/
    et patch SQLite pour renommer le projet.

Arborescence attendue :
    H:/Documents/Nathan/Photo/
    ├── 2019/
    │   ├── 2019-04-03-Soleil/
    │   │   ├── Import/         ← médias sources
    │   │   ├── Export/         ← rendus finaux
    │   │   └── ResolveProject/ ← fichiers .drp
    │   ├── 2019-05-28-Nature/
    │   └── ...
    ├── 2020/
    └── Templates/
        ├── TemplatePortrait.drp
        └── TemplatesPaysage.drp

Détection automatique de l'orientation :
    Analyse les dimensions des images dans Import/ pour choisir
    automatiquement entre Template Portrait ou Paysage.

Usage :
    python project.py                        # mode interactif
    python project.py --mode api             # force API Resolve
    python project.py --mode template        # force clonage template
    python project.py --project "2019-04-03-Soleil" --orient auto
"""

import os
import sys
import shutil
import sqlite3
import argparse
import datetime
from pathlib import Path
from typing import Literal

# ─────────────────────────────────────────────
# CONFIGURATION — adaptez ces chemins
# ─────────────────────────────────────────────

BASE_DIR        = Path(__file__).parent                     # H:/Documents/Nathan/Photo
TEMPLATES_DIR   = BASE_DIR / "Templates"

TEMPLATE_PORTRAIT  = TEMPLATES_DIR / "TemplatePortrait.drp"
TEMPLATE_PAYSAGE   = TEMPLATES_DIR / "TemplatesPaysage.drp"

# Résolutions par défaut
RESOLUTIONS = {
    "4K":    (3840, 2160),
    "2.7K":  (2704, 1520),
    "1080p": (1920, 1080),
}

# Fréquences d'images courantes
FRAMERATES = ["24", "25", "30", "50", "60"]


# ─────────────────────────────────────────────
# DÉTECTION AUTOMATIQUE DE L'ORIENTATION
# ─────────────────────────────────────────────

def detect_orientation(import_dir: Path) -> Literal["portrait", "paysage", "unknown"]:
    """
    Analyse les images dans Import/ pour déterminer l'orientation dominante.
    
    Returns:
        "portrait"  - majorité des images en portrait (hauteur > largeur)
        "paysage"   - majorité des images en paysage (largeur > hauteur)
        "unknown"   - impossible de déterminer (aucune image, ou erreur)
    """
    try:
        from PIL import Image
    except ImportError:
        print("  ⚠ Module Pillow non installé → impossible de détecter l'orientation")
        print("    Installation : pip install Pillow")
        return "unknown"
    
    if not import_dir.exists():
        return "unknown"
    
    # Extensions supportées par Pillow
    image_extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
    
    portrait_count = 0
    paysage_count = 0
    analyzed = 0
    
    print(f"\n🔍 Analyse des images dans {import_dir.name}/ ...")
    
    for img_path in import_dir.rglob("*"):
        if img_path.suffix.lower() not in image_extensions:
            continue
        
        try:
            with Image.open(img_path) as img:
                width, height = img.size
                
                # Ignorer les images carrées (ratio < 5% de différence)
                ratio = abs(width - height) / max(width, height)
                if ratio < 0.05:
                    continue
                
                if height > width:
                    portrait_count += 1
                else:
                    paysage_count += 1
                
                analyzed += 1
                
                # Limiter l'analyse aux 20 premières images pour la rapidité
                if analyzed >= 20:
                    break
        
        except Exception as e:
            # Image corrompue ou format non supporté
            continue
    
    if analyzed == 0:
        print("  ⚠ Aucune image analysable trouvée")
        return "unknown"
    
    # Déterminer l'orientation majoritaire
    orientation = "portrait" if portrait_count > paysage_count else "paysage"
    
    print(f"  ✓ {analyzed} images analysées")
    print(f"    Portrait : {portrait_count}")
    print(f"    Paysage  : {paysage_count}")
    print(f"  → Orientation détectée : {orientation.upper()}")
    
    return orientation


# ─────────────────────────────────────────────
# DÉCOUVERTE DES PROJETS EXISTANTS
# ─────────────────────────────────────────────

def find_all_projects() -> dict[str, Path]:
    """
    Scanne tous les dossiers d'années (2019, 2020, etc.) et retourne
    un dictionnaire {nom_projet: chemin_racine}.
    
    Ex: {"2019-04-03-Soleil": Path("H:/Documents/Nathan/Photo/2019/2019-04-03-Soleil")}
    """
    projects = {}
    
    for year_dir in sorted(BASE_DIR.glob("[0-9][0-9][0-9][0-9]")):
        if not year_dir.is_dir():
            continue
        
        for project_dir in sorted(year_dir.iterdir()):
            if not project_dir.is_dir():
                continue
            
            # Vérifier que la structure Import/Export/ResolveProject existe
            import_dir = project_dir / "Import"
            export_dir = project_dir / "Export"
            resolve_dir = project_dir / "ResolveProject"
            
            # Créer les dossiers manquants
            import_dir.mkdir(exist_ok=True)
            export_dir.mkdir(exist_ok=True)
            resolve_dir.mkdir(exist_ok=True)
            
            projects[project_dir.name] = project_dir
    
    return projects


def list_projects():
    """Affiche tous les projets disponibles avec leur année."""
    projects = find_all_projects()
    
    if not projects:
        print("✗ Aucun projet trouvé dans l'arborescence")
        return
    
    print("\n📁 Projets disponibles :")
    print("─" * 60)
    
    current_year = None
    for i, (name, path) in enumerate(projects.items(), 1):
        year = path.parent.name
        if year != current_year:
            print(f"\n  {year}:")
            current_year = year
        
        import_count = len(list((path / "Import").rglob("*.*"))) if (path / "Import").exists() else 0
        has_drp = any((path / "ResolveProject").glob("*.drp")) if (path / "ResolveProject").exists() else False
        
        status = "✓" if has_drp else "○"
        print(f"    {status} {i:2d}. {name}  ({import_count} fichiers dans Import/)")
    
    print("\n  Légende : ✓ = projet .drp existant | ○ = pas encore créé")
    print("─" * 60)


# ─────────────────────────────────────────────
# MODE 1 — API DAVINCI RESOLVE
# ─────────────────────────────────────────────

def get_resolve_api():
    """Tente d'importer l'API DaVinci Resolve (disponible si Resolve est ouvert)."""
    # Chemins standards Windows
    resolve_paths = [
        r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules",
        r"C:\Program Files\Blackmagic Design\DaVinci Resolve",
    ]
    for p in resolve_paths:
        if p not in sys.path:
            sys.path.append(p)

    try:
        import DaVinciResolveScript as dvr
        resolve = dvr.scriptapp("Resolve")
        if resolve:
            print("✓ API DaVinci Resolve détectée")
            return resolve
    except ImportError:
        pass

    print("✗ API DaVinci non disponible (Resolve fermé ou non installé)")
    return None


def create_project_via_api(config: dict) -> bool:
    """
    Crée un projet DaVinci Resolve complet via l'API officielle.

    config keys:
        name         str   — Nom du projet
        project_path Path  — Chemin racine du projet (contient Import/, Export/, etc.)
        resolution   tuple — (largeur, hauteur) ex: (3840, 2160)
        framerate    str   — "25", "30", etc.
        orientation  str   — "portrait" | "paysage"
    """
    resolve = get_resolve_api()
    if not resolve:
        return False

    pm = resolve.GetProjectManager()

    # Créer le projet
    project = pm.CreateProject(config["name"])
    if not project:
        print(f"✗ Impossible de créer le projet '{config['name']}' (existe déjà ?)")
        print("  → Essayez de le supprimer dans DaVinci Resolve d'abord")
        return False

    print(f"✓ Projet '{config['name']}' créé")

    # ── Paramètres de timeline ──────────────────────────
    w, h = config.get("resolution", (3840, 2160))

    # Portrait = on inverse largeur/hauteur
    if config.get("orientation") == "portrait":
        w, h = h, w

    project.SetSetting("timelineResolutionWidth",  str(w))
    project.SetSetting("timelineResolutionHeight", str(h))
    project.SetSetting("timelineFrameRate",        config.get("framerate", "25"))
    project.SetSetting("colorScienceMode",         "davinci")
    print(f"✓ Résolution : {w}×{h} @ {config.get('framerate', '25')} fps")

    # ── Media Pool — Bins ───────────────────────────────
    media_pool = project.GetMediaPool()
    root_bin   = media_pool.GetRootFolder()

    # Bins par défaut
    bins_to_create = ["Rushes", "Selects", "Exports", "Audio", "Graphics"]
    
    created_bins = {}
    for bin_name in bins_to_create:
        new_bin = media_pool.AddSubFolder(root_bin, bin_name)
        if new_bin:
            created_bins[bin_name] = new_bin
            print(f"  + Bin '{bin_name}' créé")

    # ── Import des médias depuis Import/ ────────────────
    import_dir = config["project_path"] / "Import"
    media_paths = collect_media_from_dir(import_dir)
    
    if media_paths:
        target_bin = created_bins.get("Rushes", root_bin)
        media_pool.SetCurrentFolder(target_bin)
        added = media_pool.ImportMedia(media_paths)
        print(f"✓ {len(added or [])} clips importés depuis Import/ dans 'Rushes'")
    else:
        print("  ⚠ Aucun média trouvé dans Import/")

    # ── Timeline vide ───────────────────────────────────
    timeline = media_pool.CreateEmptyTimeline(f"Timeline_{config['name']}")
    if timeline:
        print(f"✓ Timeline '{timeline.GetName()}' créée")

    print(f"\n🎬 Projet DaVinci '{config['name']}' prêt !")
    return True


# ─────────────────────────────────────────────
# MODE 2 — CLONAGE DE TEMPLATE (.drp / SQLite)
# ─────────────────────────────────────────────

def clone_template(config: dict) -> Path | None:
    """
    Clone le template .drp adapté dans ResolveProject/ et renomme le projet via SQLite.
    Retourne le chemin du nouveau .drp, ou None en cas d'erreur.
    """
    # Choisir le bon template
    orientation = config.get("orientation", "paysage").lower()
    template    = TEMPLATE_PORTRAIT if orientation == "portrait" else TEMPLATE_PAYSAGE

    if not template.exists():
        print(f"✗ Template introuvable : {template}")
        print("  → Vérifiez le dossier Templates/")
        return None

    # Dossier de destination
    resolve_dir = config["project_path"] / "ResolveProject"
    resolve_dir.mkdir(exist_ok=True)

    # Nom de destination
    project_name = config["name"]
    dest = resolve_dir / f"{project_name}.drp"

    if dest.exists():
        backup = resolve_dir / f"{project_name}_backup_{datetime.datetime.now():%Y%m%d_%H%M%S}.drp"
        dest.rename(backup)
        print(f"  ⚠ Ancienne version sauvegardée → {backup.name}")

    shutil.copy2(template, dest)
    print(f"✓ Template {orientation.upper()} copié → {dest}")

    # ── Patch SQLite ────────────────────────────────────
    try:
        _patch_drp_sqlite(dest, config)
        print(f"✓ Métadonnées mises à jour dans {dest.name}")
    except Exception as e:
        print(f"  ⚠ Patch SQLite échoué ({e}) — le fichier reste utilisable tel quel")
        print("    Renommez le projet manuellement dans DaVinci Resolve.")

    return dest


def _patch_drp_sqlite(drp_path: Path, config: dict):
    """
    Modifie les tables SQLite d'un .drp pour mettre à jour le nom et
    les paramètres de base du projet.

    Note : La structure interne des .drp varie selon la version de Resolve.
    Ce patch cible les tables communes (v18/v19).
    """
    conn = sqlite3.connect(drp_path)
    cur  = conn.cursor()

    # Lister les tables disponibles (debug)
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]

    # Tenter de renommer le projet dans les tables connues
    name = config["name"]

    rename_queries = [
        # Format DaVinci 18+
        "UPDATE Project SET Value=? WHERE Key='ProjectName'",
        "UPDATE ProjectSettings SET Value=? WHERE Key='ProjectName'",
        # Format alternatif
        "UPDATE Settings SET Value=? WHERE Key='name'",
    ]
    for q in rename_queries:
        table = q.split(" ")[1]  # extrait le nom de table
        if table in tables:
            try:
                cur.execute(q, (name,))
            except sqlite3.OperationalError:
                pass  # colonne/format différent, on ignore

    # Mise à jour résolution si table présente
    if "ProjectSettings" in tables:
        w, h = config.get("resolution", (3840, 2160))
        if config.get("orientation") == "portrait":
            w, h = h, w
        try:
            cur.execute(
                "UPDATE ProjectSettings SET Value=? WHERE Key='timelineResolutionWidth'",
                (str(w),)
            )
            cur.execute(
                "UPDATE ProjectSettings SET Value=? WHERE Key='timelineResolutionHeight'",
                (str(h),)
            )
            cur.execute(
                "UPDATE ProjectSettings SET Value=? WHERE Key='timelineFrameRate'",
                (config.get("framerate", "25"),)
            )
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# COLLECTE DES MÉDIAS
# ─────────────────────────────────────────────

PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".raw",
                    ".cr2", ".cr3", ".nef", ".arw", ".dng", ".heic"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mxf", ".avi", ".mkv", ".r3d", ".braw"}

def collect_media_from_dir(directory: Path) -> list[str]:
    """
    Retourne la liste des fichiers médias (photo/vidéo) dans un dossier.
    """
    if not directory.exists():
        return []
    
    paths = []
    all_exts = PHOTO_EXTENSIONS | VIDEO_EXTENSIONS
    
    for f in sorted(directory.rglob("*")):
        if f.is_file() and f.suffix.lower() in all_exts:
            paths.append(str(f))
    
    return paths


# ─────────────────────────────────────────────
# INTERFACE INTERACTIVE
# ─────────────────────────────────────────────

def prompt(question: str, default: str = "") -> str:
    """Input avec valeur par défaut affichée."""
    suffix = f" [{default}]" if default else ""
    val = input(f"{question}{suffix} : ").strip()
    return val if val else default


def interactive_config() -> dict:
    """Collecte interactivement les paramètres du projet."""
    print("\n" + "─"*60)
    print("  🎬  Configuration projet DaVinci Resolve")
    print("─"*60)

    # Lister les projets disponibles
    projects = find_all_projects()
    
    if not projects:
        print("✗ Aucun projet trouvé dans l'arborescence")
        print("  → Créez d'abord un dossier de projet avec la structure :")
        print("     H:/Documents/Nathan/Photo/YYYY/YYYY-MM-DD-Nom/")
        print("       ├── Import/")
        print("       ├── Export/")
        print("       └── ResolveProject/")
        sys.exit(1)
    
    list_projects()
    
    # Sélection du projet
    print("\n")
    project_names = list(projects.keys())
    
    while True:
        choice = prompt(f"Numéro du projet (1-{len(project_names)})", "1")
        if choice.isdigit() and 1 <= int(choice) <= len(project_names):
            selected_name = project_names[int(choice) - 1]
            break
        elif choice in project_names:
            selected_name = choice
            break
        else:
            print(f"  ✗ Choix invalide. Entrez un numéro entre 1 et {len(project_names)}")
    
    project_path = projects[selected_name]
    
    print(f"\n✓ Projet sélectionné : {selected_name}")
    print(f"  Chemin : {project_path}")
    
    import_count = len(collect_media_from_dir(project_path / "Import"))
    print(f"  {import_count} fichier(s) médias dans Import/")

    # Détection automatique de l'orientation
    detected_orientation = detect_orientation(project_path / "Import")
    
    # Orientation
    print("\nOrientation :")
    print("  1. Auto-détection" + (f" (→ {detected_orientation})" if detected_orientation != "unknown" else " (impossible)"))
    print("  2. Paysage (forcer)")
    print("  3. Portrait (forcer)")
    
    default_choice = "1" if detected_orientation != "unknown" else "2"
    ori_choice = prompt("Choix", default_choice)
    
    if ori_choice == "1":
        if detected_orientation == "unknown":
            print("  ⚠ Détection impossible → paysage par défaut")
            orientation = "paysage"
        else:
            orientation = detected_orientation
    elif ori_choice == "3":
        orientation = "portrait"
    else:
        orientation = "paysage"
    
    print(f"  → Orientation finale : {orientation.upper()}")

    # Résolution
    print("\nRésolution :")
    for i, (k, v) in enumerate(RESOLUTIONS.items(), 1):
        print(f"  {i}. {k}  ({v[0]}×{v[1]})")
    res_choice  = prompt("Choix", "1")
    res_key     = list(RESOLUTIONS.keys())[int(res_choice)-1 if res_choice.isdigit() else 0]
    resolution  = RESOLUTIONS[res_key]

    # Fréquence d'images
    print(f"\nFréquence d'images : {', '.join(FRAMERATES)}")
    framerate = prompt("Valeur", "25")

    return {
        "name":         selected_name,
        "project_path": project_path,
        "orientation":  orientation,
        "resolution":   resolution,
        "framerate":    framerate,
    }


# ─────────────────────────────────────────────
# POINT D'ENTRÉE
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Crée un projet DaVinci Resolve")
    parser.add_argument("--mode",    choices=["api", "template", "auto"],
                        default="auto",
                        help="api=via Resolve ouvert | template=clone .drp | auto=détection")
    parser.add_argument("--project", help="Nom du projet (ex: 2019-04-03-Soleil)")
    parser.add_argument("--orient",  choices=["portrait", "paysage", "auto"], default="auto")
    parser.add_argument("--res",     choices=list(RESOLUTIONS.keys()), default="4K")
    parser.add_argument("--fps",     default="25")
    parser.add_argument("--list",    action="store_true", help="Liste tous les projets et quitte")
    args = parser.parse_args()

    # Mode liste uniquement
    if args.list:
        list_projects()
        return

    # Mode interactif si pas de projet fourni en CLI
    if not args.project:
        config = interactive_config()
    else:
        # Mode CLI
        projects = find_all_projects()
        
        if args.project not in projects:
            print(f"✗ Projet '{args.project}' introuvable")
            print("\nProjets disponibles :")
            for name in projects.keys():
                print(f"  • {name}")
            sys.exit(1)
        
        project_path = projects[args.project]
        
        # Orientation auto-détectée si demandée
        if args.orient == "auto":
            orientation = detect_orientation(project_path / "Import")
            if orientation == "unknown":
                print("  ⚠ Détection impossible → paysage par défaut")
                orientation = "paysage"
        else:
            orientation = args.orient
        
        config = {
            "name":         args.project,
            "project_path": project_path,
            "orientation":  orientation,
            "resolution":   RESOLUTIONS[args.res],
            "framerate":    args.fps,
        }

    print(f"\n📋 Résumé du projet :")
    print(f"   Nom         : {config['name']}")
    print(f"   Chemin      : {config['project_path']}")
    
    w, h = config['resolution']
    if config['orientation'] == "portrait":
        w, h = h, w
    print(f"   Résolution  : {w}×{h} @ {config['framerate']} fps")
    print(f"   Orientation : {config['orientation'].upper()}")
    
    import_count = len(collect_media_from_dir(config['project_path'] / "Import"))
    print(f"   Médias      : {import_count} fichiers dans Import/\n")

    # Choisir le mode
    mode = args.mode
    if mode == "auto":
        resolve = get_resolve_api()
        mode    = "api" if resolve else "template"
        print()

    if mode == "api":
        success = create_project_via_api(config)
        if not success:
            print("\n→ Basculement sur le mode template...")
            result = clone_template(config)
    else:
        result = clone_template(config)
        if result:
            print(f"\n📁 Fichier prêt : {result}")
            print("   → Ouvrez DaVinci Resolve et importez ce .drp via :")
            print("      Fichier > Importer le projet...")
            print(f"\n   Les médias sont dans : {config['project_path'] / 'Import'}")
            print(f"   Les exports iront dans : {config['project_path'] / 'Export'}")


if __name__ == "__main__":
    main()
