#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_FILE="${SCRIPT_DIR}/spec-kate.xml"

if [ ! -f "$SOURCE_FILE" ]; then
    echo "Error: ${SOURCE_FILE} not found."
    exit 1
fi

DEST_DIRS=(
    "${HOME}/.local/share/org.kde.syntax-highlighting/syntax"
    "${HOME}/.local/share/katepart5/syntax"
)

for dir in "${DEST_DIRS[@]}"; do
    mkdir -p "$dir"
    cp -v "$SOURCE_FILE" "${dir}/spec.xml"
done

echo ""
echo "Spec syntax highlighting successfully installed for Kate!"
echo "Files installed to:"
for dir in "${DEST_DIRS[@]}"; do
    echo "  - ${dir}/spec.xml"
done
