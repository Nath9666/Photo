from pathlib import Path
import json
from utils.resolve import project_manager as pm
import os
from pathlib import Path
import sys
import shutil

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

TEMPLATES_DIR = BASE_DIR / "Templates"

TEMPLATE_PORTRAIT = TEMPLATES_DIR / "TemplatePortrait.drp"
TEMPLATE_PAYSAGE  = TEMPLATES_DIR / "TemplatesPaysage.drp"


def copy_template(project_path: Path, orientation: str, project_name: str):

    resolve_dir = project_path / "ResolveProject"
    resolve_dir.mkdir(exist_ok=True)

    created = []

    def _copy(template: Path, suffix: str = ""):
        if not template.exists():
            print("❌ template introuvable :", template)
            return None

        name = f"{project_name}{suffix}.drp"
        dest = resolve_dir / name

        shutil.copy2(template, dest)
        print("✔ template copié :", dest)

        return dest

    # ── CAS BOTH ─────────────────────────────
    if orientation == "both":
        p = _copy(TEMPLATE_PAYSAGE, "_paysage")
        q = _copy(TEMPLATE_PORTRAIT, "_portrait")

        if p: created.append(p)
        if q: created.append(q)

        return created

    # ── CAS SIMPLE ───────────────────────────
    template = (
        TEMPLATE_PORTRAIT
        if orientation == "portrait"
        else TEMPLATE_PAYSAGE
    )

    result = _copy(template)

    return [result] if result else []


def main():

    projects = pm.find_projects(BASE_DIR)

    print("\n📁 Projets disponibles :")
    names = list(projects.keys())

    for i, n in enumerate(names, 1):
        print(f"{i}. {n}")

    choice = int(input("\nChoix : ")) - 1
    project_name = names[choice]
    project_path = projects[project_name]

    import_dir = project_path / "Import"

    # analyse
    orientation = pm.detect_orientation(import_dir)
    resolution = pm.detect_resolution(import_dir)
    media = pm.collect_media(import_dir)

    print("\n📊 Analyse :")
    print("Orientation :", orientation)
    print("Media :", len(media))

    # split media
    portrait_media = media
    landscape_media = media

    session = {
        "project_name": project_name,
        "project_path": str(project_path),
        "orientation": orientation,
        "resolution": resolution,
        "media": media,
    }

    template_file = copy_template(project_path, orientation, project_name)

    # sauvegarde session
    session_file = project_path / "session.json"

    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2)

    print("\n✔ session créée :", session_file)

    print("\n👉 Ouvre DaVinci Resolve et lance resolve_import.py")


if __name__ == "__main__":
    main()