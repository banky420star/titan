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
