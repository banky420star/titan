#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
cd "$BASE"

mkdir -p assets docs backups logs memory/chat_history memory/sessions

STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "backups/phase16_$STAMP"

cp control_panel.py "backups/phase16_$STAMP/control_panel.py" 2>/dev/null || true
cp titan_terminal.py "backups/phase16_$STAMP/titan_terminal.py" 2>/dev/null || true
cp config.json "backups/phase16_$STAMP/config.json" 2>/dev/null || true

echo "[1/6] Creating Titan app icons..."

python3 - <<'PY'
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter
except Exception:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
    from PIL import Image, ImageDraw, ImageFilter

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
ASSETS = BASE / "assets"
ASSETS.mkdir(exist_ok=True)

def rounded_gradient_bar(size, top, bottom, radius):
    w, h = size
    img = Image.new("RGBA", size, (0,0,0,0))
    grad = Image.new("RGBA", size, (0,0,0,0))
    draw = ImageDraw.Draw(grad)
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(top[i] * (1-t) + bottom[i] * t) for i in range(3)) + (255,)
        draw.line([(0, y), (w, y)], fill=col)
    mask = Image.new("L", size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0,0,w,h], radius=radius, fill=255)
    img.alpha_composite(grad)
    img.putalpha(mask)
    return img

def make_icon(size):
    scale = size / 96
    canvas = Image.new("RGBA", (size, size), (0,0,0,0))

    # soft shadow
    shadow = Image.new("RGBA", (size, size), (0,0,0,0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse(
        [int(18*scale), int(68*scale), int(80*scale), int(84*scale)],
        fill=(0,0,0,80)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(int(5*scale)))
    canvas.alpha_composite(shadow)

    bars = [
        ("y", 10, 40, 26, 34, (255,243,161), (232,220,103), 9),
        ("o", 32, 16, 28, 58, (255,208,142), (232,171,67), 10),
        ("r", 56, 34, 26, 40, (248,176,167), (221,134,123), 9),
    ]

    for _, x, y, w, h, top, bottom, rad in bars:
        bar = rounded_gradient_bar(
            (int(w*scale), int(h*scale)),
            top,
            bottom,
            int(rad*scale)
        )
        canvas.alpha_composite(bar, (int(x*scale), int(y*scale)))

    d = ImageDraw.Draw(canvas)

    # eyes
    eye = (9, 19, 53, 255)
    for cx in [43, 57]:
        d.ellipse(
            [
                int((cx-5.8)*scale), int((49-9.2)*scale),
                int((cx+5.8)*scale), int((49+9.2)*scale)
            ],
            fill=eye
        )
        d.ellipse(
            [
                int((cx+0.3)*scale), int((45.7-1.4)*scale),
                int((cx+3.1)*scale), int((45.7+1.4)*scale)
            ],
            fill=(255,255,255,245)
        )

    return canvas

# PNG launch icon
png = make_icon(1024)
png.save(ASSETS / "titan_launch_icon.png")

# ICO favicon
ico_sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
icons = [make_icon(s[0]).resize(s, Image.LANCZOS) for s in ico_sizes]
icons[0].save(ASSETS / "favicon.ico", sizes=ico_sizes)

# SVG favicon fallback
svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">
  <defs>
    <linearGradient id="yg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#fff3a1"/><stop offset="100%" stop-color="#e8dc67"/></linearGradient>
    <linearGradient id="og" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#ffd08e"/><stop offset="100%" stop-color="#e8ab43"/></linearGradient>
    <linearGradient id="rg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#f8b0a7"/><stop offset="100%" stop-color="#dd867b"/></linearGradient>
  </defs>
  <rect x="10" y="40" width="26" height="34" rx="9" fill="url(#yg)"/>
  <rect x="32" y="16" width="28" height="58" rx="10" fill="url(#og)"/>
  <rect x="56" y="34" width="26" height="40" rx="9" fill="url(#rg)"/>
  <ellipse cx="43" cy="49" rx="5.8" ry="9.2" fill="#091335"/>
  <ellipse cx="57" cy="49" rx="5.8" ry="9.2" fill="#091335"/>
  <circle cx="44.3" cy="45.7" r="1.4" fill="white"/>
  <circle cx="58.3" cy="45.7" r="1.4" fill="white"/>
</svg>
"""
(ASSETS / "titan_favicon.svg").write_text(svg)
(ASSETS / "titan_launch_icon.svg").write_text(svg)

# macOS .icns
iconset = ASSETS / "Titan.iconset"
iconset.mkdir(exist_ok=True)

sizes = [
    (16, "icon_16x16.png"),
    (32, "icon_16x16@2x.png"),
    (32, "icon_32x32.png"),
    (64, "icon_32x32@2x.png"),
    (128, "icon_128x128.png"),
    (256, "icon_128x128@2x.png"),
    (256, "icon_256x256.png"),
    (512, "icon_256x256@2x.png"),
    (512, "icon_512x512.png"),
    (1024, "icon_512x512@2x.png"),
]

for s, name in sizes:
    make_icon(s).save(iconset / name)

try:
    subprocess.check_call(["iconutil", "-c", "icns", str(iconset), "-o", str(ASSETS / "Titan.icns")])
    print("Created:", ASSETS / "Titan.icns")
except Exception as e:
    print("iconutil failed, PNG/SVG/ICO still created:", repr(e))

print("Icon assets created.")
PY

echo "[2/6] Creating double-click Terminal launchers..."

DESKTOP="$HOME/Desktop"
APP="$BASE/Titan Terminal.app"
APP_DESKTOP="$DESKTOP/Titan Terminal.app"
COMMAND="$DESKTOP/Titan Terminal.command"

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
    <string>Titan Terminal</string>
    <key>CFBundleDisplayName</key>
    <string>Titan Terminal</string>
    <key>CFBundleIdentifier</key>
    <string>local.titan.terminal</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleExecutable</key>
    <string>TitanTerminal</string>
    <key>CFBundleIconFile</key>
    <string>Titan</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
  </dict>
</plist>
PLIST

cat > "$APP/Contents/MacOS/TitanTerminal" <<'APP'
#!/bin/zsh
osascript <<'OSA'
tell application "Terminal"
  activate
  do script "cd /Volumes/AI_DRIVE/TitanAgent && source venv/bin/activate && python3 titan_terminal.py"
end tell
OSA
APP

chmod +x "$APP/Contents/MacOS/TitanTerminal"

# Copy app to Desktop
rm -rf "$APP_DESKTOP"
ditto "$APP" "$APP_DESKTOP" 2>/dev/null || cp -R "$APP" "$APP_DESKTOP"

# Also create simple .command double-click launcher
cat > "$COMMAND" <<'CMD'
#!/bin/zsh
cd /Volumes/AI_DRIVE/TitanAgent
source venv/bin/activate
python3 titan_terminal.py
CMD

chmod +x "$COMMAND"

echo "Created:"
echo "- $APP"
echo "- $APP_DESKTOP"
echo "- $COMMAND"

echo "[3/6] Writing chat history engine..."

cat > agent_core/chat_history.py <<'PY'
from pathlib import Path
from datetime import datetime
import json
import re
import uuid

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
HISTORY_DIR = BASE / "memory" / "chat_history"
SECTION_FILE = BASE / "memory" / "current_section.txt"

HISTORY_DIR.mkdir(parents=True, exist_ok=True)
SECTION_FILE.parent.mkdir(parents=True, exist_ok=True)


def now():
    return datetime.now().isoformat(timespec="seconds")


def today_path():
    return HISTORY_DIR / (datetime.now().strftime("%Y-%m-%d") + ".jsonl")


def slug_section(value):
    value = str(value or "").strip()
    if not value:
        value = "General"
    return value[:80]


def current_section():
    if SECTION_FILE.exists():
        value = SECTION_FILE.read_text(encoding="utf-8").strip()
        if value:
            return value
    return "General"


def set_section(name):
    name = slug_section(name)
    SECTION_FILE.write_text(name, encoding="utf-8")
    log_event("system", "Section changed to: " + name, section=name, meta={"event": "section_change"})
    return "Current section: " + name


def log_event(role, content, section=None, meta=None):
    item = {
        "id": "chat-" + uuid.uuid4().hex[:10],
        "time": now(),
        "section": section or current_section(),
        "role": str(role or "system"),
        "content": str(content or ""),
        "meta": meta or {}
    }

    with today_path().open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

    return item["id"]


def iter_events():
    for path in sorted(HISTORY_DIR.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def list_sections():
    sections = {}

    for item in iter_events():
        sec = item.get("section", "General")
        sections.setdefault(sec, 0)
        sections[sec] += 1

    if current_section() not in sections:
        sections[current_section()] = 0

    return [
        {"section": name, "count": count, "active": name == current_section()}
        for name, count in sorted(sections.items(), key=lambda x: x[0].lower())
    ]


def history_list(section=None, limit=80):
    items = list(iter_events())

    if section:
        items = [x for x in items if x.get("section") == section]

    items = items[-int(limit):]
    items.reverse()

    return {
        "current_section": current_section(),
        "count": len(items),
        "items": items
    }


def history_text(section=None, limit=60):
    data = history_list(section, limit)

    if not data["items"]:
        return "No chat history found."

    lines = [f"Current section: {data['current_section']}", ""]

    for item in data["items"]:
        lines.append(
            f"{item.get('time')} | {item.get('section')} | {item.get('role')}\n"
            f"{item.get('content')}\n"
        )

    return "\n".join(lines)


def history_search(query, limit=40):
    query = str(query or "").strip()

    if not query:
        return {"query": query, "count": 0, "items": []}

    q = query.lower()
    results = []

    for item in iter_events():
        hay = (
            str(item.get("section", "")) + " " +
            str(item.get("role", "")) + " " +
            str(item.get("content", ""))
        ).lower()

        if q in hay:
            results.append(item)

    results = results[-int(limit):]
    results.reverse()

    return {
        "query": query,
        "count": len(results),
        "items": results
    }


def history_search_text(query, limit=30):
    data = history_search(query, limit)

    if not data["items"]:
        return "No history matches."

    lines = [f"History matches for: {query}", ""]

    for item in data["items"]:
        lines.append(
            f"{item.get('time')} | {item.get('section')} | {item.get('role')}\n"
            f"{item.get('content')}\n"
        )

    return "\n".join(lines)
PY

echo "[4/6] Patching Titan terminal chat logging..."

python3 - <<'PY'
from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

start = text.find("def run_titan_prompt(command):")
if start == -1:
    raise SystemExit("Could not find run_titan_prompt()")

end = text.find("\ndef repl():", start)
if end == -1:
    raise SystemExit("Could not find repl() after run_titan_prompt()")

new_func = r'''def run_titan_prompt(command):
    cmd = str(command or "").strip()
    low = cmd.lower()

    user_log_id = None
    try:
        from agent_core.chat_history import log_event
        user_log_id = log_event("user", cmd, meta={"source": "terminal"})
    except Exception:
        pass

    try:
        # Fast shortcuts: no Ollama call.
        if low in ["show me the workspace tree.", "show me the workspace tree", "workspace tree", "tree"]:
            from agent_core.tools import workspace_tree
            result = workspace_tree()
        elif low in ["list files", "show files", "list workspace files"]:
            from agent_core.tools import list_files
            result = list_files()
        elif low in ["list products", "show products", "products"]:
            from agent_core.products import list_products_text
            result = list_products_text()
        elif low in ["list skills", "show skills", "skills"]:
            from agent_core.skills import list_skills
            result = list_skills()
        elif low.startswith("read "):
            from agent_core.tools import read_file
            result = read_file(cmd[5:].strip())
        elif low.startswith("create product "):
            from agent_core.products import create_product
            name = cmd.replace("create product ", "", 1).strip()
            result = create_product(name, "python_cli", "Created from fast terminal shortcut.")
        else:
            from agent_core.agent import run_agent
            cfg = load_config()
            result = run_agent(cmd, max_steps=int(cfg.get("max_agent_steps", 5)))

        try:
            from agent_core.chat_history import log_event
            log_event("assistant", result, meta={"source": "terminal", "reply_to": user_log_id})
        except Exception:
            pass

        return result

    except Exception as e:
        result = "Titan brain failed safely: " + repr(e)
        try:
            from agent_core.chat_history import log_event
            log_event("assistant", result, meta={"source": "terminal", "reply_to": user_log_id, "error": True})
        except Exception:
            pass
        return result


def terminal_section(name):
    try:
        from agent_core.chat_history import set_section
        say_panel(set_section(name), title="Chat Section", style="green")
    except Exception as e:
        say_panel("Section failed: " + repr(e), title="Chat Section", style="red")


def terminal_sections():
    try:
        from agent_core.chat_history import list_sections
        say_panel(json.dumps(list_sections(), indent=2), title="Chat Sections", style="cyan")
    except Exception as e:
        say_panel("Sections failed: " + repr(e), title="Chat Sections", style="red")


def terminal_history(args=""):
    try:
        from agent_core.chat_history import history_text
        section = str(args or "").strip() or None
        say_panel(history_text(section=section, limit=80), title="Chat History", style="magenta")
    except Exception as e:
        say_panel("History failed: " + repr(e), title="Chat History", style="red")


def terminal_history_search(query):
    try:
        from agent_core.chat_history import history_search_text
        say_panel(history_search_text(query, limit=40), title="History Search", style="cyan")
    except Exception as e:
        say_panel("History search failed: " + repr(e), title="History Search", style="red")


'''

text = text[:start] + new_func + text[end:]

if 'lower.startswith("/section ")' not in text:
    target = '''            if lower == "/memory":
                show_memory()
                continue
'''
    replacement = '''            if lower == "/memory":
                show_memory()
                continue

            if lower.startswith("/section "):
                terminal_section(command.replace("/section ", "", 1).strip())
                continue

            if lower == "/sections":
                terminal_sections()
                continue

            if lower.startswith("/history-search "):
                terminal_history_search(command.replace("/history-search ", "", 1).strip())
                continue

            if lower.startswith("/history"):
                terminal_history(command.replace("/history", "", 1).strip())
                continue
'''
    if target in text:
        text = text.replace(target, replacement, 1)
    else:
        raise SystemExit("Could not find /memory handler insertion point.")

text = text.replace(
    "/memory      Show saved Titan memories\n",
    "/memory      Show saved Titan memories\n/section <name> Set chat/project section\n/sections    List chat sections\n/history [section]\n/history-search <query>\n"
)

path.write_text(text, encoding="utf-8")
print("Patched terminal chat history.")
PY

echo "[5/6] Patching dashboard favicon and History tab..."

python3 - <<'PY'
from pathlib import Path
import re

path = Path("control_panel.py")
text = path.read_text(encoding="utf-8")

# Ensure flask import has send_from_directory
if "send_from_directory" not in text:
    text = text.replace(
        "from flask import Flask, jsonify, render_template_string, request",
        "from flask import Flask, jsonify, render_template_string, request, send_from_directory"
    )

# Favicon links
if 'rel="icon" href="/assets/favicon.ico"' not in text:
    text = text.replace(
        "<title>Titan</title>",
        '<title>Titan</title>\n  <link rel="icon" href="/assets/favicon.ico">\n  <link rel="alternate icon" href="/assets/titan_favicon.svg">'
    )

# Nav item
if "showView('history'" not in text:
    text = text.replace(
        '<button class="active" onclick="showView(\'chat\', this)">💬 Chat</button>',
        '<button class="active" onclick="showView(\'chat\', this)">💬 Chat</button>\n'
        '        <button onclick="showView(\'history\', this); loadHistory()">▤ History</button>'
    )

# History section
if 'id="view-history"' not in text:
    section = r'''
        <section id="view-history" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Chat History / Project Sections</strong>
              <button class="btn" onclick="loadHistory()">Refresh</button>
            </div>

            <div class="panel-body">
              <div class="row">
                <input class="field" id="sectionName" placeholder="section name, e.g. Dashboard Config">
                <button class="btn primary" onclick="setHistorySection()">Set Section</button>
                <button class="btn" onclick="loadSections()">Sections</button>
              </div>

              <div class="row">
                <input class="field" id="historyQuery" placeholder="search chat history">
                <button class="btn" onclick="searchHistory()">Search</button>
              </div>

              <div class="history-layout">
                <div class="history-side">
                  <div class="section-title">Sections</div>
                  <div id="sectionsOut" class="history-list">Loading...</div>
                </div>

                <div class="history-main">
                  <div class="section-title" id="historyTitle">History</div>
                  <pre id="historyOut">Loading...</pre>
                </div>
              </div>
            </div>
          </div>
        </section>
'''
    text = text.replace('<section id="view-chat" class="view active">', section + '\n\n        <section id="view-chat" class="view active">')

# CSS
css = r'''
    /* TITAN_CHAT_HISTORY_START */
    .history-layout {
      display: grid;
      grid-template-columns: 300px 1fr;
      gap: 16px;
      min-height: 560px;
    }

    .history-side,
    .history-main {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.035);
      border-radius: 18px;
      overflow: hidden;
    }

    .history-list {
      max-height: 620px;
      overflow-y: auto;
      padding: 12px;
      display: grid;
      gap: 8px;
    }

    .history-section-item {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.045);
      border-radius: 14px;
      padding: 10px;
      cursor: pointer;
      transition: background .14s ease, transform .14s ease;
    }

    .history-section-item:hover {
      background: rgba(255,255,255,.075);
      transform: translateY(-1px);
    }

    .history-section-item.active {
      border-color: rgba(232,171,67,.38);
      background: rgba(232,171,67,.09);
    }

    .history-section-name {
      font-weight: 850;
      font-size: 13px;
    }

    .history-section-meta {
      color: var(--muted);
      font-size: 12px;
      margin-top: 4px;
    }

    #historyOut {
      max-height: 620px;
      overflow-y: auto;
      margin: 14px;
      padding: 14px;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: rgba(0,0,0,.18);
    }

    @media (max-width: 980px) {
      .history-layout {
        grid-template-columns: 1fr;
      }
    }
    /* TITAN_CHAT_HISTORY_END */
'''

if "TITAN_CHAT_HISTORY_START" not in text:
    text = text.replace("</style>", css + "\n  </style>", 1)

# JS
js = r'''
// TITAN_CHAT_HISTORY_JS_START
async function loadSections() {
  const data = await jsonFetch("/api/history/sections");
  const out = document.getElementById("sectionsOut");
  if (!out) return;

  const sections = data.sections || [];

  if (!sections.length) {
    out.textContent = "No sections yet.";
    return;
  }

  out.innerHTML = "";

  sections.forEach(sec => {
    const div = document.createElement("div");
    div.className = "history-section-item" + (sec.active ? " active" : "");
    div.onclick = () => loadHistory(sec.section);

    const name = document.createElement("div");
    name.className = "history-section-name";
    name.textContent = sec.section;

    const meta = document.createElement("div");
    meta.className = "history-section-meta";
    meta.textContent = `${sec.count} entries` + (sec.active ? " · active" : "");

    div.appendChild(name);
    div.appendChild(meta);
    out.appendChild(div);
  });
}

function renderHistoryItems(items) {
  if (!items || !items.length) return "No chat history found.";

  return items.map(item => {
    return `${item.time || ""} | ${item.section || "General"} | ${item.role || ""}\n${item.content || ""}\n`;
  }).join("\n");
}

async function loadHistory(section = "") {
  await loadSections();

  const url = "/api/history" + (section ? "?section=" + encodeURIComponent(section) : "");
  const data = await jsonFetch(url);

  const title = document.getElementById("historyTitle");
  const out = document.getElementById("historyOut");

  if (title) title.textContent = section ? "History: " + section : "History";
  if (out) out.textContent = renderHistoryItems(data.items || []);
}

async function searchHistory() {
  const q = document.getElementById("historyQuery").value.trim();
  const out = document.getElementById("historyOut");
  const title = document.getElementById("historyTitle");

  if (!q) {
    if (out) out.textContent = "Enter a search query.";
    return;
  }

  const data = await jsonFetch("/api/history/search?q=" + encodeURIComponent(q));

  if (title) title.textContent = "History Search: " + q;
  if (out) out.textContent = renderHistoryItems(data.items || []);
}

async function setHistorySection() {
  const name = document.getElementById("sectionName").value.trim();
  if (!name) {
    titanToast("Section missing", "Enter a section name.", "warn");
    return;
  }

  const data = await jsonFetch("/api/history/section", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({section: name})
  });

  titanToast("Section changed", data.result || name, "success");
  await loadSections();
  await loadHistory(name);
}
// TITAN_CHAT_HISTORY_JS_END
'''

if "TITAN_CHAT_HISTORY_JS_START" not in text:
    text = text.replace("</script>", js + "\n</script>", 1)

# Patch task logging in dashboard backend
if "TITAN_HISTORY_START_JOB_PATCH" not in text:
    text = text.replace(
        "def start_job(task):\n    job_id = make_job_id()",
        '''def start_job(task):
    # TITAN_HISTORY_START_JOB_PATCH
    try:
        from agent_core.chat_history import log_event
        history_user_id = log_event("user", task, meta={"source": "dashboard"})
    except Exception:
        history_user_id = None

    job_id = make_job_id()'''
    )

    text = text.replace(
        '''        "max_steps": 8
    }''',
        '''        "max_steps": 8,
        "history_user_id": history_user_id
    }''',
        1
    )

if "TITAN_HISTORY_READ_JOB_PATCH" not in text:
    text = text.replace(
        '''            data = json.loads(path.read_text(encoding="utf-8"))
            trace = TRACES / f"{job_id}.trace.md"''',
        '''            data = json.loads(path.read_text(encoding="utf-8"))

            # TITAN_HISTORY_READ_JOB_PATCH
            if data.get("status") in ["done", "error"] and data.get("result") and not data.get("history_logged"):
                try:
                    from agent_core.chat_history import log_event
                    log_event("assistant", data.get("result", ""), meta={"source": "dashboard", "job_id": job_id, "reply_to": data.get("history_user_id")})
                    data["history_logged"] = True
                    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                except Exception:
                    pass

            trace = TRACES / f"{job_id}.trace.md"'''
    )

# Routes
routes = r'''
@app.route("/api/history")
def api_history():
    from agent_core.chat_history import history_list
    return safe(lambda: history_list(request.args.get("section") or None, int(request.args.get("limit", 100))))


@app.route("/api/history/search")
def api_history_search():
    from agent_core.chat_history import history_search
    return safe(lambda: history_search(request.args.get("q", ""), int(request.args.get("limit", 60))))


@app.route("/api/history/sections")
def api_history_sections():
    from agent_core.chat_history import list_sections
    return safe(lambda: {"sections": list_sections()})


@app.route("/api/history/section", methods=["POST"])
def api_history_section():
    from agent_core.chat_history import set_section
    return safe(lambda: {"result": set_section(request.json.get("section", "General"))})

'''

if '@app.route("/api/history")' not in text:
    text = text.replace('\n\nif __name__ == "__main__":', "\n\n" + routes + '\nif __name__ == "__main__":')

# Assets route
if '@app.route("/assets/<path:name>")' not in text:
    route = '''
@app.route("/assets/<path:name>")
def titan_assets(name):
    return send_from_directory(str(BASE / "assets"), name)

'''
    text = text.replace('\n\nif __name__ == "__main__":', "\n\n" + route + '\nif __name__ == "__main__":')

path.write_text(text, encoding="utf-8")
print("Patched dashboard history and favicon.")
PY

echo "[6/6] Verifying..."

python3 -m py_compile agent_core/chat_history.py titan_terminal.py control_panel.py

cat > docs/PHASE16_LAUNCHER_FAVICON_HISTORY.md <<EOF
# Phase 16 Launcher, Favicon, and Chat History

Timestamp: $STAMP

Added:
- Titan Terminal.app
- Desktop Titan Terminal.app
- Desktop Titan Terminal.command
- assets/Titan.icns
- assets/titan_launch_icon.png
- assets/titan_launch_icon.svg
- assets/titan_favicon.svg
- assets/favicon.ico
- agent_core/chat_history.py
- dashboard History tab
- chat sections
- terminal history commands

Terminal commands:
- /section <name>
- /sections
- /history [section]
- /history-search <query>

Dashboard:
- History tab
- section switching
- history search
- favicon installed

Launchers:
- $BASE/Titan Terminal.app
- $HOME/Desktop/Titan Terminal.app
- $HOME/Desktop/Titan Terminal.command

Next:
- app launcher for dashboard
- session export
- markdown project logs
EOF

echo ""
echo "Phase 16 complete."
echo ""
echo "Double-click launchers:"
echo "- $HOME/Desktop/Titan Terminal.app"
echo "- $HOME/Desktop/Titan Terminal.command"
echo ""
echo "Restart dashboard:"
echo "lsof -ti :5050 | xargs kill -9 2>/dev/null || true"
echo "python3 launch_dashboard.py"
