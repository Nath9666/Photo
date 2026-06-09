# ─────────────────────────────
# RESOLVE CONTEXT (injecté par Resolve)
# Ce script est lancé depuis l'intérieur de DaVinci Resolve.
# L'objet `resolve` est injecté automatiquement par l'application.
# ─────────────────────────────

import json
from pathlib import Path

# Racine du workspace Photo : utils/resolve/ → utils/ → Photo/
BASE_DIR = Path(r"H:\Photo")


def find_session(base: Path):
    for f in base.rglob("session.json"):
        return f
    return None


def main():

    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject()

    if not project:
        print("❌ aucun projet ouvert dans DaVinci Resolve")
        return

    session_path = find_session(BASE_DIR)

    if not session_path:
        print("❌ aucune session.json trouvée dans", BASE_DIR)
        return

    data = json.loads(session_path.read_text(encoding="utf-8"))

    # Pour le cas "both", détecter l'orientation depuis le nom du projet ouvert
    orientation = data["orientation"]
    current_name = project.GetName()

    if orientation == "both":
        orientation = "portrait" if "_portrait" in current_name else "paysage"

    w, h = data["resolution"]

    if orientation == "portrait":
        w, h = h, w

    project.SetSetting("timelineResolutionWidth", str(w))
    project.SetSetting("timelineResolutionHeight", str(h))
    project.SetSetting("timelineFrameRate", "25")

    media_key = "portrait_media" if orientation == "portrait" else "landscape_media"
    media = data.get(media_key, data.get("media", []))

    media_pool = project.GetMediaPool()
    root = media_pool.GetRootFolder()

    bin_rush = media_pool.AddSubFolder(root, "Rushes")
    media_pool.SetCurrentFolder(bin_rush)
    media_pool.ImportMedia(media)

    print(f"   {len(media)} fichier(s) importé(s) ({orientation})")

    media_pool.CreateEmptyTimeline("Timeline_01")

    print("✔ import terminé dans le projet :", current_name)


if __name__ == "__main__":
    main()