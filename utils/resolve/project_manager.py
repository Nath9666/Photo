# project_manager.py
from pathlib import Path
from typing import Literal, Tuple
import os

PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mxf", ".avi", ".mkv", ".r3d", ".braw"}

RESOLUTIONS = {
    "4K": (3840, 2160),
    "2.7K": (2704, 1520),
    "1080p": (1920, 1080),
}


def collect_media(import_dir: Path) -> list[str]:
    """Retourne tous les médias du dossier Import/"""
    if not import_dir.exists():
        return []

    exts = PHOTO_EXTENSIONS | VIDEO_EXTENSIONS
    return [
        str(f)
        for f in import_dir.rglob("*")
        if f.is_file() and f.suffix.lower() in exts
    ]


def split_media_by_orientation(import_dir: Path) -> tuple[list[str], list[str]]:
    """Retourne (portrait_media, landscape_media).
    Les vidéos et fichiers non analysables sont placés dans les deux listes."""
    try:
        from PIL import Image
    except ImportError:
        all_media = collect_media(import_dir)
        return all_media, all_media

    portrait: list[str] = []
    landscape: list[str] = []

    for f in import_dir.rglob("*"):
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if ext in VIDEO_EXTENSIONS:
            portrait.append(str(f))
            landscape.append(str(f))
            continue
        if ext not in PHOTO_EXTENSIONS:
            continue
        try:
            with Image.open(f) as im:
                w, h = im.size
            if h > w:
                portrait.append(str(f))
            else:
                landscape.append(str(f))
        except Exception:
            portrait.append(str(f))
            landscape.append(str(f))

    return portrait, landscape


def detect_orientation(import_dir: Path) -> Literal["portrait", "paysage", "both", "unknown"]:
    """Analyse simple des images pour orientation dominante"""
    try:
        from PIL import Image
    except ImportError:
        return "unknown"

    if not import_dir.exists():
        return "unknown"

    portrait = 0
    landscape = 0
    checked = 0

    for img in import_dir.rglob("*"):
        if img.suffix.lower() not in PHOTO_EXTENSIONS:
            continue

        try:
            with Image.open(img) as im:
                w, h = im.size

                if abs(w - h) / max(w, h) < 0.05:
                    continue

                if h > w:
                    portrait += 1
                else:
                    landscape += 1

                checked += 1
                if checked >= 20:
                    break
        except:
            continue

    if checked == 0:
        return "unknown"
    if portrait > 0 and landscape > 0:
        return "both"
    return "portrait" if portrait > landscape else "paysage"


def detect_resolution(import_dir: Path) -> tuple[int, int]:
    """Estime résolution max des images"""
    try:
        from PIL import Image
    except ImportError:
        return RESOLUTIONS["4K"]

    max_dim = 0

    for img in import_dir.rglob("*"):
        if img.suffix.lower() not in PHOTO_EXTENSIONS:
            continue

        try:
            with Image.open(img) as im:
                w, h = im.size
                max_dim = max(max_dim, w, h)
        except:
            continue

    if max_dim >= 3840:
        return RESOLUTIONS["4K"]
    if max_dim >= 2704:
        return RESOLUTIONS["2.7K"]
    return RESOLUTIONS["1080p"]


def find_projects(base_dir: Path) -> dict[str, Path]:
    """Scan structure YYYY/YYYY-project"""
    projects = {}

    for year in sorted(base_dir.glob("[0-9][0-9][0-9][0-9]")):
        if not year.is_dir():
            continue

        for proj in year.iterdir():
            if proj.is_dir():
                projects[proj.name] = proj

    return projects