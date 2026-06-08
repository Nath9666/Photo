# ─────────────────────────────
# RESOLVE CONTEXT (injecté par Resolve)
# ─────────────────────────────

project = resolve.GetProjectManager().GetCurrentProject()

import json
from pathlib import Path

def load_session():

    base = Path(r"H:\Documents\Nathan\Photo")

    for f in base.rglob("session.json"):
        return f

    return None


def main():

    session_path = load_session()

    if not session_path:
        print("❌ aucune session trouvée")
        return

    data = json.loads(session_path.read_text(encoding="utf-8"))

    pm = resolve.GetProjectManager()

    name = data["project_name"]
    project = pm.CreateProject(name)

    if not project:
        print("❌ projet existe déjà")
        return

    w, h = data["resolution"]

    if data["orientation"] == "portrait":
        w, h = h, w

    project.SetSetting("timelineResolutionWidth", str(w))
    project.SetSetting("timelineResolutionHeight", str(h))
    project.SetSetting("timelineFrameRate", "25")

    media_pool = project.GetMediaPool()
    root = media_pool.GetRootFolder()

    bin_rush = media_pool.AddSubFolder(root, "Rushes")

    media_pool.SetCurrentFolder(bin_rush)
    media_pool.ImportMedia(data["media"])

    media_pool.CreateEmptyTimeline("Timeline_01")

    print("✔ projet Resolve créé :", name)


if __name__ == "__main__":
    main()