import os
import sys
from datetime import datetime

# ── Config ──────────────────────────────────────────────
BASE_DIR = "."
OUTPUT_FILE = "CHANGELOG.md"
YEAR_MIN = 2000
YEAR_MAX = 2100
# ────────────────────────────────────────────────────────

def is_year_dir(name):
    return name.isdigit() and YEAR_MIN <= int(name) <= YEAR_MAX

def check_project(project_path):
    resolve_dir = os.path.join(project_path, "ResolveProject")
    export_dir  = os.path.join(project_path, "Export")
    has_drp    = False
    has_export = False
    if os.path.isdir(resolve_dir):
        has_drp = any(f.endswith(".drp") for f in os.listdir(resolve_dir))
    if os.path.isdir(export_dir):
        has_export = any(
            os.path.isfile(os.path.join(export_dir, f))
            for f in os.listdir(export_dir)
        )
    return {"done": has_drp and has_export, "has_drp": has_drp, "has_export": has_export}

def scan_projects(base_dir):
    result = {}
    for year_name in sorted(os.listdir(base_dir)):
        if not is_year_dir(year_name):
            continue
        year_path = os.path.join(base_dir, year_name)
        if not os.path.isdir(year_path):
            continue
        projects = []
        for project_name in sorted(os.listdir(year_path)):
            project_path = os.path.join(year_path, project_name)
            if not os.path.isdir(project_path):
                continue
            projects.append({"name": project_name, "path": project_path, "status": check_project(project_path)})
        if projects:
            result[year_name] = projects
    return result

def status_icon(status):
    if status["done"]:                              return "✅"
    if status["has_drp"] and not status["has_export"]: return "🔧"
    if not status["has_drp"]:                       return "⏳"
    return "❓"

def status_label(status):
    if status["done"]:                              return "Terminé"
    if status["has_drp"] and not status["has_export"]: return "En cours — export manquant"
    if not status["has_drp"]:                       return "À faire — pas de projet Resolve"
    return "Statut inconnu"

def build_snapshot(projects_by_year, now_str):
    """Construit le bloc markdown d'une exécution."""
    total = sum(len(v) for v in projects_by_year.values())
    done  = sum(1 for v in projects_by_year.values() for p in v if p["status"]["done"])
    lines = []
    lines.append(f"## Snapshot — {now_str}")
    lines.append(f"**{done}/{total} projets terminés** — {total - done} restant(s)\n")
    for year, projects in sorted(projects_by_year.items(), reverse=True):
        year_done = sum(1 for p in projects if p["status"]["done"])
        lines.append(f"### {year}  ({year_done}/{len(projects)})\n")
        for p in projects:
            lines.append(f"- {status_icon(p['status'])} `{p['name']}` — {status_label(p['status'])}")
        lines.append("")
    return "\n".join(lines)

def read_existing(output_path):
    """Récupère le contenu des snapshots précédents (sans l'en-tête fixe)."""
    if not os.path.exists(output_path):
        return ""
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    marker = "---\n"
    idx = content.find(marker)
    return content[idx + len(marker):] if idx != -1 else content

def write_changelog(output_path, snapshot, previous_content):
    header = (
        "# Suivi des retouches\n\n"
        "> Ce fichier est généré automatiquement. "
        "Chaque exécution ajoute un nouveau snapshot.\n\n"
        "---\n"
    )
    separator = "\n---\n\n"
    body = snapshot + (separator + previous_content.strip() if previous_content.strip() else "")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header + "\n" + body + "\n")

def main():
    base_dir = os.path.abspath(BASE_DIR)
    print(f"📂 Scan de : {base_dir}\n")
    projects_by_year = scan_projects(base_dir)
    if not projects_by_year:
        print("Aucun dossier année trouvé. Lance le script depuis la racine du repo.")
        sys.exit(1)

    total = sum(len(v) for v in projects_by_year.values())
    done  = sum(1 for v in projects_by_year.values() for p in v if p["status"]["done"])
    print(f"✅  Terminés   : {done}")
    print(f"⏳  À faire    : {sum(1 for v in projects_by_year.values() for p in v if not p['status']['has_drp'])}")
    print(f"🔧  En cours   : {sum(1 for v in projects_by_year.values() for p in v if p['status']['has_drp'] and not p['status']['done'])}")
    print(f"─── Total      : {total}\n")

    now_str          = datetime.now().strftime("%Y-%m-%d %H:%M")
    output_path      = os.path.join(base_dir, OUTPUT_FILE)
    previous_content = read_existing(output_path)
    snapshot         = build_snapshot(projects_by_year, now_str)
    write_changelog(output_path, snapshot, previous_content)
    print(f"📝 CHANGELOG.md mis à jour : {output_path}")

if __name__ == "__main__":
    main()