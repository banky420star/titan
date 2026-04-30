#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
cd "$BASE"

mkdir -p assets docs/project_logs backups logs memory/chat_history

STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "backups/phase17_$STAMP"

cp control_panel.py "backups/phase17_$STAMP/control_panel.py" 2>/dev/null || true
cp titan_terminal.py "backups/phase17_$STAMP/titan_terminal.py" 2>/dev/null || true

echo "[1/5] Creating double-click Dashboard launchers..."

DESKTOP="$HOME/Desktop"
APP="$BASE/Titan Dashboard.app"
APP_DESKTOP="$DESKTOP/Titan Dashboard.app"
COMMAND="$DESKTOP/Titan Dashboard.command"

rm -rf "$APP"

mkdir -p "$APP/Contents/MacOS"
mkdir -p "$APP/Contents/Resources"

cp "$BASE/assets/Titan.icns" "$APP/Contents/Resources/Titan.icns" 2>/dev/null || true

cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "https://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>CFBundleName</key>
    <string>Titan Dashboard</string>
    <key>CFBundleDisplayName</key>
    <string>Titan Dashboard</string>
    <key>CFBundleIdentifier</key>
    <string>local.titan.dashboard</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleExecutable</key>
    <string>TitanDashboard</string>
    <key>CFBundleIconFile</key>
    <string>Titan</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
  </dict>
</plist>
PLIST

cat > "$APP/Contents/MacOS/TitanDashboard" <<'APP'
#!/bin/zsh
cd /Volumes/AI_DRIVE/TitanAgent
source venv/bin/activate
python3 launch_dashboard.py >> logs/dashboard_app_launcher.log 2>&1
APP

chmod +x "$APP/Contents/MacOS/TitanDashboard"

rm -rf "$APP_DESKTOP"
ditto "$APP" "$APP_DESKTOP" 2>/dev/null || cp -R "$APP" "$APP_DESKTOP"

cat > "$COMMAND" <<'CMD'
#!/bin/zsh
cd /Volumes/AI_DRIVE/TitanAgent
source venv/bin/activate
python3 launch_dashboard.py
CMD

chmod +x "$COMMAND"

echo "Created:"
echo "- $APP"
echo "- $APP_DESKTOP"
echo "- $COMMAND"

echo "[2/5] Writing history export engine..."

cat > agent_core/chat_export.py <<'PY'
from pathlib import Path
from datetime import datetime
import re

from agent_core.chat_history import history_list, list_sections, current_section

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
EXPORTS = BASE / "docs" / "project_logs"
EXPORTS.mkdir(parents=True, exist_ok=True)


def slug(value):
    value = str(value or "").strip() or "all-history"
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value)
    return value.strip("-") or "history"


def export_history(section=None, limit=10000):
    section = str(section or "").strip() or None
    data = history_list(section=section, limit=limit)
    items = list(reversed(data.get("items", [])))

    label = section or "all-history"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORTS / f"{slug(label)}_{stamp}.md"

    lines = [
        f"# Titan Chat History: {label}",
        "",
        f"Exported: {datetime.now().isoformat(timespec='seconds')}",
        f"Current section: {data.get('current_section', current_section())}",
        f"Entries: {len(items)}",
        "",
        "---",
        ""
    ]

    for item in items:
        role = item.get("role", "unknown")
        sec = item.get("section", "General")
        time = item.get("time", "")
        content = str(item.get("content", ""))

        lines.append(f"## {time} · {sec} · {role}")
        lines.append("")
        lines.append(content)
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "result": "exported",
        "section": label,
        "entries": len(items),
        "path": str(path)
    }


def export_all_sections():
    outputs = []
    sections = list_sections()

    for item in sections:
        name = item.get("section")
        outputs.append(export_history(name))

    return {
        "result": "exported sections",
        "count": len(outputs),
        "exports": outputs
    }
PY

echo "[3/5] Patching terminal export command..."

python3 - <<'PY'
from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

if "def terminal_export_history(" not in text:
    marker = "def repl():"
    if marker not in text:
        raise SystemExit("Could not find def repl()")

    helpers = r'''
def terminal_export_history(args=""):
    try:
        from agent_core.chat_export import export_history, export_all_sections

        section = str(args or "").strip()

        if section.lower() == "all-sections":
            result = export_all_sections()
        else:
            result = export_history(section or None)

        say_panel(json.dumps(result, indent=2), title="History Export", style="green")
    except Exception as e:
        say_panel("History export failed: " + repr(e), title="History Export", style="red")


'''
    text = text.replace(marker, helpers + marker)

if 'lower.startswith("/export-history")' not in text:
    target = '''            if lower.startswith("/history"):
                terminal_history(command.replace("/history", "", 1).strip())
                continue
'''
    replacement = target + '''
            if lower.startswith("/export-history"):
                terminal_export_history(command.replace("/export-history", "", 1).strip())
                continue
'''
    if target not in text:
        raise SystemExit("Could not find /history handler block.")

    text = text.replace(target, replacement, 1)

text = text.replace(
    "/history-search <query>\n",
    "/history-search <query>\n/export-history [section|all-sections]\n"
)

path.write_text(text, encoding="utf-8")
print("Patched terminal export command.")
PY

echo "[4/5] Patching dashboard History export + Cmd+K..."

python3 - <<'PY'
from pathlib import Path
import re

path = Path("control_panel.py")
text = path.read_text(encoding="utf-8")

# Add export button to History row.
if "exportHistory()" not in text:
    text = text.replace(
        '<button class="btn" onclick="loadSections()">Sections</button>',
        '<button class="btn" onclick="loadSections()">Sections</button>\n'
        '                <button class="btn" onclick="exportHistory()">Export Current</button>\n'
        '                <button class="btn" onclick="exportAllSections()">Export All Sections</button>',
        1
    )

# Add JS functions.
js = r'''
// TITAN_HISTORY_EXPORT_JS_START
async function exportHistory(section = "") {
  const active = document.querySelector(".history-section-item.active .history-section-name");
  const chosen = section || (active ? active.textContent : "");

  const data = await jsonFetch("/api/history/export", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({section: chosen})
  });

  titanToast("History exported", data.path || data.result || "Export complete.", "success", 6500);

  const out = document.getElementById("historyOut");
  if (out) out.textContent = JSON.stringify(data, null, 2);
}

async function exportAllSections() {
  const data = await jsonFetch("/api/history/export-all", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({})
  });

  titanToast("All sections exported", `${data.count || 0} exports created.`, "success", 6500);

  const out = document.getElementById("historyOut");
  if (out) out.textContent = JSON.stringify(data, null, 2);
}
// TITAN_HISTORY_EXPORT_JS_END
'''

if "TITAN_HISTORY_EXPORT_JS_START" not in text:
    text = text.replace("</script>", js + "\n</script>", 1)

# Add routes.
routes = r'''
@app.route("/api/history/export", methods=["POST"])
def api_history_export():
    from agent_core.chat_export import export_history
    return safe(lambda: export_history(request.json.get("section") or None))


@app.route("/api/history/export-all", methods=["POST"])
def api_history_export_all():
    from agent_core.chat_export import export_all_sections
    return safe(lambda: export_all_sections())

'''

if '@app.route("/api/history/export")' not in text:
    text = text.replace('\n\nif __name__ == "__main__":', "\n\n" + routes + '\nif __name__ == "__main__":')

# Add Cmd+K commands.
if 'title: "Export History"' not in text:
    needle = '''  {
    title: "Refresh History",
    desc: "Reload chat history and sections.",
    keywords: "refresh history sections logs",
    run: () => loadHistory()
  },'''
    insert = '''  {
    title: "Refresh History",
    desc: "Reload chat history and sections.",
    keywords: "refresh history sections logs",
    run: () => loadHistory()
  },
  {
    title: "Export History",
    desc: "Export the current chat history section to Markdown.",
    keywords: "export history markdown project logs sections",
    run: () => { clickNavByView("history"); exportHistory(); }
  },
  {
    title: "Export All History Sections",
    desc: "Export every chat history section to Markdown.",
    keywords: "export all history sections markdown logs",
    run: () => { clickNavByView("history"); exportAllSections(); }
  },'''
    if needle in text:
        text = text.replace(needle, insert, 1)
    else:
        print("Could not find Refresh History command block; skipped Cmd+K export commands.")

path.write_text(text, encoding="utf-8")
print("Patched dashboard history export.")
PY

echo "[5/5] Verifying..."

python3 -m py_compile agent_core/chat_export.py titan_terminal.py control_panel.py

cat > docs/PHASE17_DASHBOARD_LAUNCHER_HISTORY_EXPORT.md <<EOF
# Phase 17 Dashboard Launcher and History Export

Timestamp: $STAMP

Added:
- Titan Dashboard.app
- Desktop Titan Dashboard.app
- Desktop Titan Dashboard.command
- agent_core/chat_export.py
- /export-history [section|all-sections]
- dashboard History export buttons
- Cmd+K export history commands

Launchers:
- $BASE/Titan Dashboard.app
- $HOME/Desktop/Titan Dashboard.app
- $HOME/Desktop/Titan Dashboard.command

Exports:
- docs/project_logs/*.md

Next:
- product templates
- Git integration
- session timeline
EOF

echo ""
echo "Phase 17 complete."
echo ""
echo "Double-click dashboard launcher:"
echo "- $HOME/Desktop/Titan Dashboard.app"
echo "- $HOME/Desktop/Titan Dashboard.command"
