import os
import sys
import io
from datetime import datetime
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    from PIL import Image
except ImportError:
    print("Installation de Pillow...")
    os.system(f"{sys.executable} -m pip install Pillow")
    from PIL import Image

# ── Config ──────────────────────────────────────────────
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".cr2", ".nef", ".arw", ".dng", ".webp"}
EXPORT_DIR_NAME  = "Export"
README_FILENAME  = "README.md"
BASE_SIZE        = 250
# ────────────────────────────────────────────────────────

def get_image_dimensions(filepath):
    try:
        with Image.open(filepath) as img:
            return img.size
    except Exception:
        return (None, None)

def compute_display_size(w, h):
    if w is None or h is None:
        return BASE_SIZE, BASE_SIZE
    if w <= h:  # portrait → largeur fixe
        ratio = BASE_SIZE / w
    else:       # paysage → hauteur fixe
        ratio = BASE_SIZE / h
    return round(w * ratio), round(h * ratio)

def find_all_exports(base_dir):
    projects = []
    for year_entry in sorted(os.scandir(base_dir), key=lambda e: e.name):
        if not year_entry.is_dir() or not year_entry.name.isdigit():
            continue
        for project_entry in sorted(os.scandir(year_entry.path), key=lambda e: e.name):
            if not project_entry.is_dir():
                continue
            export_path = os.path.join(project_entry.path, EXPORT_DIR_NAME)
            if not os.path.isdir(export_path):
                continue

            photos = []
            for f in sorted(os.scandir(export_path), key=lambda e: e.name):
                if not f.is_file():
                    continue
                if os.path.splitext(f.name)[1].lower() not in PHOTO_EXTENSIONS:
                    continue
                w, h   = get_image_dimensions(f.path)
                dw, dh = compute_display_size(w, h)
                photos.append({
                    "name":     f.name,
                    "rel_path": os.path.relpath(f.path, base_dir).replace("\\", "/"),
                    "width":    dw,
                    "height":   dh,
                })

            projects.append({
                "year":    year_entry.name,
                "album":   project_entry.name,
                "photos":  photos,
                "count":   len(photos),
            })
    return projects

def build_readme(projects, base_dir):
    now          = datetime.now().strftime("%d/%m/%Y à %Hh%M")
    total_photos = sum(p["count"] for p in projects)
    by_year      = defaultdict(list)
    for p in projects:
        by_year[p["year"]].append(p)

    lines = []

    # ── En-tête ───────────────────────────────────────────
    lines += [
        "# 📷 Récapitulatif des exports",
        "",
        f"> Généré le {now} · **{len(projects)} projet(s)** · **{total_photos} photo(s)**",
        "",
        "---",
        "",
    ]

    # ── Sections par année ────────────────────────────────
    for year, year_projects in sorted(by_year.items()):
        lines += [f"## {year}", ""]

        for p in year_projects:
            lines += [
                f"### 🗂️ {p['album']}",
                f"📸 **{p['count']} photo(s)**",
                "",
            ]

            if p["photos"]:
                # Ouverture du conteneur flex
                lines.append('<div style="display:flex; flex-wrap:wrap; gap:10px; align-items:flex-end;">')
                lines.append("")

                for photo in p["photos"]:
                    lines.append(
                        f'<img src="{photo["rel_path"]}" '
                        f'width="{photo["width"]}" '
                        f'height="{photo["height"]}" '
                        f'alt="{photo["name"]}" '
                        f'title="{photo["name"]}" '
                        f'style="border-radius:4px; object-fit:cover;">'
                    )

                lines += ["", "</div>", ""]
            else:
                lines += ["*Aucune photo dans ce dossier Export.*", ""]

            lines.append("---")
            lines.append("")

    return "\n".join(lines)

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))

    print(base_dir)

    print("\n🔍 Scan des dossiers Export en cours...\n")
    projects = find_all_exports(base_dir)

    if not projects:
        print("❌ Aucun projet trouvé.")
        sys.exit(1)

    by_year = defaultdict(list)
    for p in projects:
        by_year[p["year"]].append(p)

    for year, year_projects in sorted(by_year.items()):
        print(f"📅 {year}")
        for p in year_projects:
            status = f"{p['count']} photo(s)" if p["count"] else "⚠️  vide"
            print(f"   └─ {p['album']:<45} {status}")
        print()

    total = sum(p["count"] for p in projects)
    print(f"✅ {len(projects)} projet(s) · {total} photo(s)\n")

    readme_path = os.path.join(base_dir, README_FILENAME)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(build_readme(projects, base_dir))

    print(f"📝 README.md généré : {readme_path}\n")

if __name__ == "__main__":
    main()