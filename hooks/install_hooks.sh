#!/bin/sh
# Lance ce script une fois après avoir cloné le repo
# pour activer les git hooks versionnés.

HOOKS_DIR="$(git rev-parse --show-toplevel)/.git/hooks"
SOURCE_DIR="$(git rev-parse --show-toplevel)/hooks"

echo "🔧 Installation des git hooks..."

for hook in "$SOURCE_DIR"/*; do
    name=$(basename "$hook")
    dest="$HOOKS_DIR/$name"

    cp "$hook" "$dest"
    chmod +x "$dest"
    echo "  ✅ $name installé"
done

echo "\n🎉 Hooks installés. Ils se déclencheront automatiquement à chaque commit."
