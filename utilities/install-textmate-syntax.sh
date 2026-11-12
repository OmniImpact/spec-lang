#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_SOURCE="${SCRIPT_DIR}/textmate/spec"
DEST_DIR="${HOME}/.local/share/spec/textmate/spec"

if [ ! -d "$BUNDLE_SOURCE" ]; then
    echo "Error: ${BUNDLE_SOURCE} not found."
    exit 1
fi

echo "Installing Spec TextMate bundle to: ${DEST_DIR}"
mkdir -p "$DEST_DIR"
cp -r "${BUNDLE_SOURCE}/"* "$DEST_DIR/"

# 1. Register in JetBrains IDEs
JB_CONFIG="${HOME}/.config/JetBrains"
if [ -d "$JB_CONFIG" ]; then
    echo "Registering in JetBrains IDEs..."
    python3 - <<EOF
import os, glob, json, re

bundle_path = "${DEST_DIR}"
config_dir = os.path.expanduser("${JB_CONFIG}")

for ide_dir in glob.glob(os.path.join(config_dir, "*")):
    if not os.path.isdir(ide_dir):
        continue
    ide_name = os.path.basename(ide_dir)
    options_dir = os.path.join(ide_dir, "options")
    os.makedirs(options_dir, exist_ok=True)
    xml_path = os.path.join(options_dir, "textmate.xml")

    if os.path.exists(xml_path):
        with open(xml_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = '<application>\n</application>\n'

    pattern = r'<component name="TextMateUserBundlesSettings">(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</component>'
    match = re.search(pattern, content, re.DOTALL)
    data = {}
    if match:
        raw_json = match.group(1).strip()
        try:
            data = json.loads(raw_json)
        except Exception:
            data = {}

    if not isinstance(data, dict):
        data = {}
    if "bundles" not in data or not isinstance(data["bundles"], dict):
        data = {"bundles": {}}

    data["bundles"][bundle_path] = {"name": "spec-syntax", "enabled": True}
    json_str = json.dumps(data)
    new_comp = f'<component name="TextMateUserBundlesSettings"><![CDATA[{json_str}]]></component>'

    if match:
        new_content = content[:match.start()] + new_comp + content[match.end():]
    else:
        app_end = content.rfind("</application>")
        if app_end != -1:
            new_content = content[:app_end] + f'  {new_comp}\n' + content[app_end:]
        else:
            new_content = f'<application>\n  {new_comp}\n</application>\n'

    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"  - Configured {ide_name} ({xml_path})")
EOF
fi

# 2. Register in VS Code (if ~/.vscode exists)
VSCODE_EXT_DIR="${HOME}/.vscode/extensions"
if [ -d "${HOME}/.vscode" ]; then
    echo "Registering in VS Code..."
    mkdir -p "$VSCODE_EXT_DIR"
    ln -sfn "$DEST_DIR" "${VSCODE_EXT_DIR}/spec-syntax"
    echo "  - Symlinked to ${VSCODE_EXT_DIR}/spec-syntax"
fi

echo ""
echo "Spec TextMate bundle installed successfully!"
echo "Note: If your JetBrains IDE is currently open, please restart it or reload TextMate bundles (Settings -> Editor -> TextMate Bundles)."
