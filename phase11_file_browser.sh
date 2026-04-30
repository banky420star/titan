#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
cd "$BASE"

mkdir -p agent_core docs backups logs workspace products skills rag/docs downloads

STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "backups/phase11_$STAMP"

cp control_panel.py "backups/phase11_$STAMP/control_panel.py" 2>/dev/null || true

echo "[1/4] Writing agent_core/file_browser.py..."

cat > agent_core/file_browser.py <<'PY'
from pathlib import Path
from datetime import datetime
import json

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")

ROOTS = {
    "workspace": BASE / "workspace",
    "products": BASE / "products",
    "skills": BASE / "skills",
    "rag": BASE / "rag" / "docs",
    "docs": BASE / "docs",
    "downloads": BASE / "downloads",
}

TEXT_SUFFIXES = {
    ".txt", ".md", ".py", ".json", ".yaml", ".yml",
    ".html", ".css", ".js", ".ts", ".tsx", ".jsx",
    ".sh", ".zsh", ".sql", ".csv", ".toml", ".ini",
    ".env", ".gitignore"
}

for root in ROOTS.values():
    root.mkdir(parents=True, exist_ok=True)


def root_path(root_name):
    root_name = str(root_name or "workspace").strip()

    if root_name not in ROOTS:
        raise ValueError("Unknown root: " + root_name)

    root = ROOTS[root_name].resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def safe_path(root_name, rel_path=""):
    root = root_path(root_name)
    rel = Path(str(rel_path or "").strip())

    if rel.is_absolute():
        raise ValueError("Absolute paths are not allowed.")

    target = (root / rel).resolve()

    if target != root and not str(target).startswith(str(root) + "/"):
        raise ValueError("Path escapes allowed root.")

    return root, target


def file_info(root, path):
    stat = path.stat()
    return {
        "name": path.name,
        "path": str(path.relative_to(root)),
        "type": "dir" if path.is_dir() else "file",
        "size": stat.st_size if path.is_file() else None,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "text": path.is_file() and (path.suffix.lower() in TEXT_SUFFIXES or path.suffix == "")
    }


def list_dir(root_name="workspace", rel_path=""):
    root, target = safe_path(root_name, rel_path)

    if not target.exists():
        return {
            "root": root_name,
            "path": str(rel_path or ""),
            "error": "Path not found."
        }

    if not target.is_dir():
        target = target.parent

    dirs = []
    files = []

    for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        if item.name.startswith(".DS_Store"):
            continue

        info = file_info(root, item)

        if item.is_dir():
            dirs.append(info)
        else:
            files.append(info)

    parent = ""
    if target != root:
        parent = str(target.parent.relative_to(root))

    return {
        "root": root_name,
        "path": str(target.relative_to(root)) if target != root else "",
        "parent": parent,
        "items": dirs + files,
        "roots": list(ROOTS.keys())
    }


def read_file(root_name="workspace", rel_path=""):
    root, target = safe_path(root_name, rel_path)

    if not target.exists():
        return {"error": "File not found."}

    if target.is_dir():
        return {"error": "Path is a folder."}

    if target.stat().st_size > 2_000_000:
        return {"error": "File too large for dashboard editor."}

    if target.suffix.lower() not in TEXT_SUFFIXES and target.suffix != "":
        return {"error": "Not a supported text file type."}

    return {
        "root": root_name,
        "path": str(target.relative_to(root)),
        "content": target.read_text(encoding="utf-8", errors="ignore"),
        "size": target.stat().st_size,
        "modified": datetime.fromtimestamp(target.stat().st_mtime).isoformat(timespec="seconds")
    }


def write_file(root_name="workspace", rel_path="", content=""):
    if root_name == "downloads":
        return {"error": "Downloads root is read-only from dashboard editor."}

    root, target = safe_path(root_name, rel_path)

    if target.exists() and target.is_dir():
        return {"error": "Cannot write over a folder."}

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(str(content or ""), encoding="utf-8")

    return {
        "result": "saved",
        "root": root_name,
        "path": str(target.relative_to(root)),
        "size": target.stat().st_size
    }


def make_dir(root_name="workspace", rel_path=""):
    if root_name == "downloads":
        return {"error": "Downloads root is read-only from dashboard editor."}

    root, target = safe_path(root_name, rel_path)
    target.mkdir(parents=True, exist_ok=True)

    return {
        "result": "folder created",
        "root": root_name,
        "path": str(target.relative_to(root))
    }
PY

echo "[2/4] Patching control_panel.py..."

cat > patch_dashboard_file_browser.py <<'PY'
from pathlib import Path
import re

path = Path("control_panel.py")
text = path.read_text(encoding="utf-8")

# Add nav item.
if "showView('files'" not in text:
    text = text.replace(
        '<button onclick="showView(\'jobs\', this); loadJobs()">▣ Jobs</button>',
        '<button onclick="showView(\'jobs\', this); loadJobs()">▣ Jobs</button>\n'
        '        <button onclick="showView(\'files\', this); loadFiles()">🗂 Files</button>'
    )

# Add file browser view before skills view.
if 'id="view-files"' not in text:
    files_section = r'''
        <section id="view-files" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>File Browser</strong>
              <div class="row compact-row">
                <select class="field small-field" id="fileRoot" onchange="changeFileRoot()">
                  <option value="workspace">workspace</option>
                  <option value="products">products</option>
                  <option value="skills">skills</option>
                  <option value="rag">rag/docs</option>
                  <option value="docs">docs</option>
                  <option value="downloads">downloads</option>
                </select>
                <button class="btn" onclick="loadFiles()">Refresh</button>
                <button class="btn" onclick="fileUp()">Up</button>
              </div>
            </div>

            <div class="panel-body">
              <div class="file-path" id="filePath">/</div>

              <div class="files-layout">
                <div class="file-list-wrap">
                  <div class="section-title">Files</div>
                  <div id="fileList" class="file-list">Loading...</div>
                </div>

                <div class="file-editor-wrap">
                  <div class="section-title" id="editorTitle">No file selected</div>

                  <div class="row">
                    <input class="field" id="newFilePath" placeholder="new file path, e.g. notes/todo.md">
                    <button class="btn" onclick="createFileFromInput()">New File</button>
                  </div>

                  <div class="row">
                    <input class="field" id="newFolderPath" placeholder="new folder path, e.g. notes">
                    <button class="btn" onclick="createFolderFromInput()">New Folder</button>
                  </div>

                  <textarea id="fileEditor" class="file-editor" placeholder="Open or create a text file..."></textarea>

                  <div class="row">
                    <button class="btn primary" onclick="saveOpenFile()">Save</button>
                    <button class="btn" onclick="reloadOpenFile()">Reload</button>
                  </div>

                  <pre id="fileStatus"></pre>
                </div>
              </div>
            </div>
          </div>
        </section>
'''
    text = text.replace('<section id="view-skills" class="view">', files_section + '\n\n        <section id="view-skills" class="view">')

# Add CSS.
css = r'''
    /* TITAN_FILE_BROWSER_START */
    .small-field {
      max-width: 180px;
      min-width: 150px;
      height: 40px;
    }

    .file-path {
      color: var(--muted);
      margin-bottom: 12px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 13px;
    }

    .files-layout {
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 16px;
      min-height: 620px;
    }

    .file-list-wrap,
    .file-editor-wrap {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.035);
      border-radius: 18px;
      overflow: hidden;
    }

    .file-list {
      max-height: 680px;
      overflow-y: auto;
      padding: 12px;
      display: grid;
      gap: 8px;
    }

    .file-item {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.045);
      border-radius: 14px;
      padding: 10px 11px;
      cursor: pointer;
      transition: background .14s ease, transform .14s ease, border-color .14s ease;
    }

    .file-item:hover {
      background: rgba(255,255,255,.075);
      transform: translateY(-1px);
    }

    .file-item.active {
      border-color: rgba(232,171,67,.38);
      background: rgba(232,171,67,.09);
    }

    .file-name {
      font-weight: 800;
      font-size: 13px;
      display: flex;
      gap: 8px;
      align-items: center;
    }

    .file-meta {
      color: var(--muted);
      font-size: 12px;
      margin-top: 4px;
    }

    .file-editor-wrap {
      padding-bottom: 14px;
    }

    .file-editor-wrap .row {
      padding: 0 14px;
    }

    .file-editor {
      width: calc(100% - 28px);
      min-height: 390px;
      margin: 0 14px 14px;
      padding: 14px;
      border-radius: 16px;
      border: 1px solid var(--line);
      outline: none;
      resize: vertical;
      background: rgba(0,0,0,.20);
      color: #f4f4f5;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 13px;
      line-height: 1.45;
    }

    #fileStatus {
      margin: 0 14px;
      max-height: 150px;
      overflow-y: auto;
      color: var(--muted);
    }

    @media (max-width: 980px) {
      .files-layout {
        grid-template-columns: 1fr;
      }

      .file-list {
        max-height: 320px;
      }
    }
    /* TITAN_FILE_BROWSER_END */
'''

if "TITAN_FILE_BROWSER_START" not in text:
    text = text.replace("</style>", css + "\n  </style>", 1)

# Add JS.
js = r'''
// TITAN_FILE_BROWSER_JS_START
let currentFileRoot = "workspace";
let currentFilePath = "";
let currentOpenFile = "";

async function changeFileRoot() {
  currentFileRoot = document.getElementById("fileRoot").value;
  currentFilePath = "";
  currentOpenFile = "";
  document.getElementById("fileEditor").value = "";
  document.getElementById("editorTitle").textContent = "No file selected";
  await loadFiles();
}

async function loadFiles(pathOverride = null) {
  if (pathOverride !== null) currentFilePath = pathOverride;

  const rootEl = document.getElementById("fileRoot");
  if (rootEl) currentFileRoot = rootEl.value;

  const url = `/api/files?root=${encodeURIComponent(currentFileRoot)}&path=${encodeURIComponent(currentFilePath)}`;
  const data = await jsonFetch(url);

  const filePath = document.getElementById("filePath");
  const fileList = document.getElementById("fileList");

  if (filePath) filePath.textContent = `${data.root || currentFileRoot}:/${data.path || ""}`;

  if (data.error) {
    fileList.textContent = data.error;
    return;
  }

  fileList.innerHTML = "";

  if (!data.items || !data.items.length) {
    fileList.textContent = "Empty folder.";
    return;
  }

  data.items.forEach(item => {
    const div = document.createElement("div");
    div.className = "file-item" + (item.path === currentOpenFile ? " active" : "");
    div.onclick = () => {
      if (item.type === "dir") {
        openFolder(item.path);
      } else {
        openFile(item.path);
      }
    };

    const name = document.createElement("div");
    name.className = "file-name";
    name.textContent = (item.type === "dir" ? "📁 " : "📄 ") + item.name;

    const meta = document.createElement("div");
    meta.className = "file-meta";
    meta.textContent = item.type + (item.size !== null && item.size !== undefined ? ` · ${item.size} bytes` : "") + ` · ${item.modified || ""}`;

    div.appendChild(name);
    div.appendChild(meta);
    fileList.appendChild(div);
  });
}

async function openFolder(path) {
  currentFilePath = path || "";
  await loadFiles(currentFilePath);
}

async function fileUp() {
  const parts = String(currentFilePath || "").split("/").filter(Boolean);
  parts.pop();
  currentFilePath = parts.join("/");
  await loadFiles(currentFilePath);
}

async function openFile(path) {
  currentOpenFile = path;
  const data = await jsonFetch(`/api/file?root=${encodeURIComponent(currentFileRoot)}&path=${encodeURIComponent(path)}`);

  const editor = document.getElementById("fileEditor");
  const title = document.getElementById("editorTitle");
  const status = document.getElementById("fileStatus");

  if (data.error) {
    status.textContent = data.error;
    return;
  }

  title.textContent = `${currentFileRoot}:/${data.path}`;
  editor.value = data.content || "";
  status.textContent = `Opened ${data.path} · ${data.size} bytes · ${data.modified}`;
  await loadFiles();
}

async function saveOpenFile() {
  const status = document.getElementById("fileStatus");

  if (!currentOpenFile) {
    status.textContent = "No file selected.";
    return;
  }

  const content = document.getElementById("fileEditor").value;

  const data = await jsonFetch("/api/file/save", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      root: currentFileRoot,
      path: currentOpenFile,
      content
    })
  });

  status.textContent = JSON.stringify(data, null, 2);
  await loadFiles();
}

async function reloadOpenFile() {
  if (currentOpenFile) await openFile(currentOpenFile);
}

async function createFileFromInput() {
  const input = document.getElementById("newFilePath");
  const status = document.getElementById("fileStatus");
  const rel = input.value.trim();

  if (!rel) {
    status.textContent = "Enter a file path.";
    return;
  }

  const base = currentFilePath ? currentFilePath + "/" : "";
  currentOpenFile = base + rel;

  const data = await jsonFetch("/api/file/save", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      root: currentFileRoot,
      path: currentOpenFile,
      content: ""
    })
  });

  status.textContent = JSON.stringify(data, null, 2);
  input.value = "";
  await loadFiles();
  await openFile(currentOpenFile);
}

async function createFolderFromInput() {
  const input = document.getElementById("newFolderPath");
  const status = document.getElementById("fileStatus");
  const rel = input.value.trim();

  if (!rel) {
    status.textContent = "Enter a folder path.";
    return;
  }

  const base = currentFilePath ? currentFilePath + "/" : "";
  const folderPath = base + rel;

  const data = await jsonFetch("/api/folder/create", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      root: currentFileRoot,
      path: folderPath
    })
  });

  status.textContent = JSON.stringify(data, null, 2);
  input.value = "";
  await loadFiles();
}
// TITAN_FILE_BROWSER_JS_END
'''

if "TITAN_FILE_BROWSER_JS_START" not in text:
    text = text.replace("</script>", js + "\n</script>", 1)

# Add backend routes before if __name__ main.
routes = r'''
@app.route("/api/files")
def api_files():
    from agent_core.file_browser import list_dir
    return safe(lambda: list_dir(request.args.get("root", "workspace"), request.args.get("path", "")))


@app.route("/api/file")
def api_file():
    from agent_core.file_browser import read_file
    return safe(lambda: read_file(request.args.get("root", "workspace"), request.args.get("path", "")))


@app.route("/api/file/save", methods=["POST"])
def api_file_save():
    from agent_core.file_browser import write_file
    return safe(lambda: write_file(request.json.get("root", "workspace"), request.json.get("path", ""), request.json.get("content", "")))


@app.route("/api/folder/create", methods=["POST"])
def api_folder_create():
    from agent_core.file_browser import make_dir
    return safe(lambda: make_dir(request.json.get("root", "workspace"), request.json.get("path", "")))

'''

if '@app.route("/api/files")' not in text:
    text = text.replace('\n\nif __name__ == "__main__":', "\n\n" + routes + '\nif __name__ == "__main__":')

path.write_text(text, encoding="utf-8")
print("Patched dashboard file browser.")
PY

python3 patch_dashboard_file_browser.py
python3 -m py_compile agent_core/file_browser.py control_panel.py

cat > docs/PHASE11_FILE_BROWSER.md <<EOF
# Phase 11 File Browser

Timestamp: $STAMP

Added:
- agent_core/file_browser.py
- dashboard Files tab
- browse workspace/products/skills/rag/docs/docs/downloads
- open text files
- save text files
- create files
- create folders

APIs:
- GET /api/files
- GET /api/file
- POST /api/file/save
- POST /api/folder/create

Backup:
- backups/phase11_$STAMP/control_panel.py

Next:
- product launcher
- workspace full search
- file diff viewer
EOF

echo "Phase 11 complete."
