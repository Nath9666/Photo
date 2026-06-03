import os
import shutil
import sys

BASE_DIR = "."
DEST_DIR = "_A_retouche"

YEAR_MIN = 2000
YEAR_MAX = 2100

PHOTO_EXTENSIONS = {
    ".jpg", ".jpeg",
    ".png",
    ".tif", ".tiff",
    ".cr2", ".cr3",
    ".nef", ".arw",
    ".dng", ".raf",
    ".rw2", ".orf",
    ".pef", ".srw"
}


def is_year_dir(name):
    return (
        name.isdigit()
        and YEAR_MIN <= int(name) <= YEAR_MAX
    )


def is_photo(filename):
    return (
        os.path.splitext(filename)[1].lower()
        in PHOTO_EXTENSIONS
    )


def project_is_todo(project_path):
    resolve_dir = os.path.join(
        project_path,
        "ResolveProject"
    )

    if not os.path.isdir(resolve_dir):
        return True

    return not any(
        f.lower().endswith(".drp")
        for f in os.listdir(resolve_dir)
    )


def unique_destination(dest_dir, filename):
    path = os.path.join(dest_dir, filename)

    if not os.path.exists(path):
        return path

    base, ext = os.path.splitext(filename)
    index = 1

    while True:
        candidate = os.path.join(
            dest_dir,
            f"{base}_{index}{ext}"
        )

        if not os.path.exists(candidate):
            return candidate

        index += 1


def move_project_images(project_path, dest_dir):
    moved = 0

    for root, dirs, files in os.walk(project_path):

        dirs[:] = [
            d for d in dirs
            if d not in {"ResolveProject", "Export"}
        ]

        for file in files:
            if not is_photo(file):
                continue

            source = os.path.join(root, file)
            destination = unique_destination(
                dest_dir,
                file
            )

            shutil.move(source, destination)
            moved += 1

    return moved


def main():
    base_dir = os.path.abspath(BASE_DIR)

    destination_dir = os.path.join(
        base_dir,
        DEST_DIR
    )

    os.makedirs(destination_dir, exist_ok=True)

    total_projects = 0
    total_images = 0

    for year_name in sorted(os.listdir(base_dir)):

        if not is_year_dir(year_name):
            continue

        year_path = os.path.join(
            base_dir,
            year_name
        )

        if not os.path.isdir(year_path):
            continue

        for project_name in sorted(os.listdir(year_path)):

            project_path = os.path.join(
                year_path,
                project_name
            )

            if not os.path.isdir(project_path):
                continue

            if not project_is_todo(project_path):
                continue

            moved = move_project_images(
                project_path,
                destination_dir
            )

            total_projects += 1
            total_images += moved

            print(
                f"📁 {project_name} : "
                f"{moved} image(s) déplacée(s)"
            )

    print()
    print(f"📂 Projets à faire : {total_projects}")
    print(f"🖼️ Images déplacées : {total_images}")
    print(f"✅ Destination : {destination_dir}")


if __name__ == "__main__":
    main()