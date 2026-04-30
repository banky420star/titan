#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
cd "$BASE"

mkdir -p agent_core memory/file_snapshots docs backups logs

STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "backups/phase13_$STAMP"

cp control_panel.py "backups/phase13_$STAMP/control_panel.py" 2>/dev/null || true
cp titan_terminal.py "backups/phase13_$STAMP/titan_terminal.py" 2>/dev/null || true

echo "[1/4] Writing agent_core/search_diff.py..."

cat > agent_core/search_diff.py <<'PY'
from pathlib import Path
from datetime import datetime
import difflib
import json
import re

from agent_core.file_browser import ROOTS, TEXT_SUFFIXES, safe_path, root_path

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
SNAPSHOTS = BASE / "memory" / "file_snapshots"
SNAPSHOTS.mkdir(parents=True, exist_ok=True)

MAX_TEXT_SIZE = 1_500_000


def is_text_file(path):
    return path.is_file() and (path.suffix.lower() in TEXT_SUFFIXES or path.suffix == "")


def read_text_safe(path):
    try:
        if path.stat().st_size > MAX_TEXT_SIZE:
            return None
        if not is_text_file(path):
            return None
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


def compact(text, limit=900):
    text = str(text or "")
    if len(text) <= limit:
        return text
    return text[:limit] + "\n[TRUNCATED]"


def search_files(query, root="all", max_results=80):
    query = str(query or "").strip()
    root = str(root or "all").strip()

    if not query:
        return {"error": "No search query provided."}

    q = query.lower()

    roots = ROOTS.keys() if root == "all" else [root]
    results = []

    for root_name in roots:
        try:
            root_dir = root_path(root_name)
        except Exception:
            continue

        for path in sorted(root_dir.rglob("*")):
            if len(results) >= int(max_results):
                break

            if path.is_dir():
                continue

            try:
                rel = str(path.relative_to(root_dir))
                name_hit = q in path.name.lower() or q in rel.lower()

                content_hit = False
                snippet = ""

                text = read_text_safe(path)
                if text is not None and q in text.lower():
                    content_hit = True
                    idx = text.lower().find(q)
                    start = max(0, idx - 180)
                    end = min(len(text), idx + 420)
                    snippet = text[start:end].strip()

                if name_hit or content_hit:
                    results.append({
                        "root": root_name,
                        "path": rel,
                        "name": path.name,
                        "match": "name/path" if name_hit and not content_hit else "content" if content_hit and not name_hit else "name/path+content",
                        "size": path.stat().st_size,
                        "snippet": compact(snippet, 700)
                    })

            except Exception:
                continue

    return {
        "query": query,
        "root": root,
        "count": len(results),
        "results": results
    }


def search_files_text(query, root="all"):
    data = search_files(query, root=root)

    if data.get("error"):
        return data["error"]

    if not data["results"]:
        return "No matching files found."

    lines = [f"Search: {data['query']} | Root: {data['root']} | Results: {data['count']}", ""]

    for item in data["results"]:
        lines.append(
            f"{item['root']}:/{item['path']}\n"
            f"  match: {item['match']} | size: {item['size']}"
        )
        if item.get("snippet"):
            lines.append("  snippet: " + item["snippet"].replace("\n", "\n           "))
        lines.append("")

    return "\n".join(lines)


def snapshot_path(root="workspace"):
    root = str(root or "workspace").strip()
    return SNAPSHOTS / f"{root}.json"


def make_snapshot(root="workspace"):
    root = str(root or "workspace").strip()

    if root not in ROOTS:
        return {"error": "Unknown root: " + root}

    root_dir = root_path(root)
    files = {}

    for path in sorted(root_dir.rglob("*")):
        if not path.is_file():
            continue

        text = read_text_safe(path)
        if text is None:
            continue

        rel = str(path.relative_to(root_dir))
        files[rel] = text

    data = {
        "root": root,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "files": files
    }

    snapshot_path(root).write_text(json.dumps(data), encoding="utf-8")

    return {
        "result": "snapshot saved",
        "root": root,
        "files": len(files),
        "path": str(snapshot_path(root))
    }


def load_snapshot(root="workspace"):
    path = snapshot_path(root)

    if not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def changed_files(root="workspace"):
    root = str(root or "workspace").strip()

    if root not in ROOTS:
        return {"error": "Unknown root: " + root}

    snap = load_snapshot(root)

    if not snap:
        return {"error": f"No snapshot found for root: {root}. Run /snapshot {root} first."}

    root_dir = root_path(root)
    old_files = snap.get("files", {})
    current_files = {}

    for path in sorted(root_dir.rglob("*")):
        if not path.is_file():
            continue

        text = read_text_safe(path)
        if text is None:
            continue

        current_files[str(path.relative_to(root_dir))] = text

    changed = []

    all_paths = sorted(set(old_files.keys()) | set(current_files.keys()))

    for rel in all_paths:
        old = old_files.get(rel)
        new = current_files.get(rel)

        if old is None:
            status = "added"
        elif new is None:
            status = "deleted"
        elif old != new:
            status = "modified"
        else:
            continue

        changed.append({
            "root": root,
            "path": rel,
            "status": status
        })

    return {
        "root": root,
        "snapshot_created_at": snap.get("created_at"),
        "count": len(changed),
        "changed": changed
    }


def changed_files_text(root="workspace"):
    data = changed_files(root)

    if data.get("error"):
        return data["error"]

    if not data["changed"]:
        return f"No changed files since snapshot for root: {root}"

    lines = [
        f"Changed files for root: {root}",
        f"Snapshot: {data.get('snapshot_created_at')}",
        ""
    ]

    for item in data["changed"]:
        lines.append(f"- {item['status']}: {item['root']}:/{item['path']}")

    return "\n".join(lines)


def diff_file(root="workspace", rel_path=""):
    root = str(root or "workspace").strip()
    rel_path = str(rel_path or "").strip()

    if root not in ROOTS:
        return "Unknown root: " + root

    if not rel_path:
        return "No file path provided."

    snap = load_snapshot(root)

    if not snap:
        return f"No snapshot found for root: {root}. Run /snapshot {root} first."

    root_dir, target = safe_path(root, rel_path)
    current = read_text_safe(target) if target.exists() else ""

    old = snap.get("files", {}).get(rel_path)

    if old is None and current == "":
        return "File is not present in snapshot or current root: " + rel_path

    if old is None:
        old = ""

    old_lines = old.splitlines(keepends=True)
    new_lines = str(current or "").splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"snapshot/{root}/{rel_path}",
        tofile=f"current/{root}/{rel_path}",
        lineterm=""
    )

    diff_text = "".join(diff)

    if not diff_text.strip():
        return "No diff for: " + rel_path

    if len(diff_text) > 16000:
        diff_text = diff_text[:16000] + "\n\n[TRUNCATED DIFF]"

    return diff_text
PY

echo "[2/4] Patching terminal commands..."

cat > patch_terminal_search_diff.py <<'PY'
from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

if "def terminal_search_files(" not in text:
    marker = "def repl():"
    if marker not in text:
        raise SystemExit("Could not find def repl()")

    helpers = r'''
def terminal_search_files(query):
    try:
        from agent_core.search_diff import search_files_text
        say_panel(search_files_text(query, root="all"), title="Search", style="cyan")
    except Exception as e:
        say_panel("Search failed: " + repr(e), title="Search", style="red")


def terminal_snapshot(root):
    try:
        from agent_core.search_diff import make_snapshot
        root = str(root or "").strip() or "workspace"
        say_panel(json.dumps(make_snapshot(root), indent=2), title="Snapshot", style="green")
    except Exception as e:
        say_panel("Snapshot failed: " + repr(e), title="Snapshot", style="red")


def terminal_changed(root):
    try:
        from agent_core.search_diff import changed_files_text
        root = str(root or "").strip() or "workspace"
        say_panel(changed_files_text(root), title="Changed Files", style="yellow")
    except Exception as e:
        say_panel("Changed files failed: " + repr(e), title="Changed Files", style="red")


def terminal_diff(args):
    try:
        from agent_core.search_diff import diff_file
        parts = str(args or "").strip().split(" ", 1)

        if len(parts) == 1:
            root = "workspace"
            path = parts[0]
        else:
            root, path = parts

        say_panel(diff_file(root, path), title="Diff", style="magenta")
    except Exception as e:
        say_panel("Diff failed: " + repr(e), title="Diff", style="red")


'''
    text = text.replace(marker, helpers + marker)

if 'lower.startswith("/search ")' not in text:
    target = '''            if lower == "/products":
                terminal_products()
                continue
'''

    replacement = '''            if lower == "/products":
                terminal_products()
                continue

            if lower.startswith("/search "):
                terminal_search_files(command.replace("/search ", "", 1).strip())
                continue

            if lower.startswith("/snapshot"):
                terminal_snapshot(command.replace("/snapshot", "", 1).strip())
                continue

            if lower.startswith("/changed"):
                terminal_changed(command.replace("/changed", "", 1).strip())
                continue

            if lower.startswith("/diff "):
                terminal_diff(command.replace("/diff ", "", 1).strip())
                continue
'''

    if target not in text:
        raise SystemExit("Could not find insertion point for search commands.")

    text = text.replace(target, replacement, 1)

text = text.replace(
    "/products    Show products\n",
    "/products    Show products\n/search <query> Search files by name/content\n/snapshot [root] Save file snapshot\n/changed [root] Show changed files\n/diff <root> <path> Show unified diff\n"
)

path.write_text(text, encoding="utf-8")
print("Patched terminal search/diff commands.")
PY

python3 patch_terminal_search_diff.py

echo "[3/4] Patching dashboard Search / Diff tab..."

cat > patch_dashboard_search_diff.py <<'PY'
from pathlib import Path
import re

path = Path("control_panel.py")
text = path.read_text(encoding="utf-8")

if "showView('search'" not in text:
    text = text.replace(
        '<button onclick="showView(\'files\', this); loadFiles()">🗂 Files</button>',
        '<button onclick="showView(\'files\', this); loadFiles()">🗂 Files</button>\n'
        '        <button onclick="showView(\'search\', this)">🔎 Search / Diff</button>'
    )

if 'id="view-search"' not in text:
    section = r'''
        <section id="view-search" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Search / Diff</strong>
              <button class="btn" onclick="searchFiles()">Search</button>
            </div>

            <div class="panel-body">
              <div class="row">
                <select class="field small-field" id="searchRoot">
                  <option value="all">all</option>
                  <option value="workspace">workspace</option>
                  <option value="products">products</option>
                  <option value="skills">skills</option>
                  <option value="rag">rag/docs</option>
                  <option value="docs">docs</option>
                  <option value="downloads">downloads</option>
                </select>
                <input class="field" id="searchQuery" placeholder="search file names or content">
                <button class="btn primary" onclick="searchFiles()">Search</button>
              </div>

              <div class="row">
                <select class="field small-field" id="snapshotRoot">
                  <option value="workspace">workspace</option>
                  <option value="products">products</option>
                  <option value="skills">skills</option>
                  <option value="rag">rag/docs</option>
                  <option value="docs">docs</option>
                </select>
                <button class="btn" onclick="makeSnapshot()">Snapshot</button>
                <button class="btn" onclick="showChanged()">Changed</button>
              </div>

              <div class="search-layout">
                <div class="search-results-wrap">
                  <div class="section-title">Results</div>
                  <div id="searchResults" class="search-results">Search results will appear here.</div>
                </div>

                <div class="diff-wrap">
                  <div class="section-title" id="diffTitle">Diff</div>
                  <pre id="diffOut">Select a changed file or search result.</pre>
                </div>
              </div>
            </div>
          </div>
        </section>
'''
    text = text.replace('<section id="view-files" class="view">', section + '\n\n        <section id="view-files" class="view">')

css = r'''
    /* TITAN_SEARCH_DIFF_START */
    .search-layout {
      display: grid;
      grid-template-columns: 380px 1fr;
      gap: 16px;
      min-height: 600px;
    }

    .search-results-wrap,
    .diff-wrap {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.035);
      border-radius: 18px;
      overflow: hidden;
    }

    .search-results {
      max-height: 680px;
      overflow-y: auto;
      padding: 12px;
      display: grid;
      gap: 10px;
    }

    .search-item {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.045);
      border-radius: 16px;
      padding: 12px;
      cursor: pointer;
      transition: background .14s ease, transform .14s ease;
    }

    .search-item:hover {
      background: rgba(255,255,255,.075);
      transform: translateY(-1px);
    }

    .search-title {
      font-weight: 850;
      font-size: 13px;
      margin-bottom: 6px;
    }

    .search-meta {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 8px;
    }

    .search-snippet {
      color: #d4d4d8;
      font-size: 12px;
      line-height: 1.4;
      white-space: pre-wrap;
    }

    #diffOut {
      max-height: 680px;
      overflow-y: auto;
      margin: 14px;
      padding: 14px;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: rgba(0,0,0,.18);
    }

    @media (max-width: 980px) {
      .search-layout {
        grid-template-columns: 1fr;
      }
    }
    /* TITAN_SEARCH_DIFF_END */
'''

if "TITAN_SEARCH_DIFF_START" not in text:
    text = text.replace("</style>", css + "\n  </style>", 1)

js = r'''
// TITAN_SEARCH_DIFF_JS_START
async function searchFiles() {
  const root = document.getElementById("searchRoot").value;
  const q = document.getElementById("searchQuery").value.trim();
  const out = document.getElementById("searchResults");

  if (!q) {
    out.textContent = "Enter a search query.";
    return;
  }

  const data = await jsonFetch(`/api/search?root=${encodeURIComponent(root)}&q=${encodeURIComponent(q)}`);

  if (data.error) {
    out.textContent = data.error;
    return;
  }

  const results = data.results || [];

  if (!results.length) {
    out.textContent = "No results.";
    return;
  }

  out.innerHTML = "";

  results.forEach(item => {
    const div = document.createElement("div");
    div.className = "search-item";
    div.onclick = () => loadDiff(item.root, item.path);

    const title = document.createElement("div");
    title.className = "search-title";
    title.textContent = `${item.root}:/${item.path}`;

    const meta = document.createElement("div");
    meta.className = "search-meta";
    meta.textContent = `${item.match} · ${item.size} bytes`;

    const snippet = document.createElement("div");
    snippet.className = "search-snippet";
    snippet.textContent = item.snippet || "Click to diff against snapshot.";

    div.appendChild(title);
    div.appendChild(meta);
    div.appendChild(snippet);
    out.appendChild(div);
  });
}

async function makeSnapshot() {
  const root = document.getElementById("snapshotRoot").value;
  const out = document.getElementById("diffOut");
  const data = await jsonFetch("/api/snapshot", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({root})
  });
  out.textContent = JSON.stringify(data, null, 2);
}

async function showChanged() {
  const root = document.getElementById("snapshotRoot").value;
  const out = document.getElementById("searchResults");
  const data = await jsonFetch(`/api/changed?root=${encodeURIComponent(root)}`);

  if (data.error) {
    out.textContent = data.error;
    return;
  }

  const changed = data.changed || [];

  if (!changed.length) {
    out.textContent = "No changed files.";
    return;
  }

  out.innerHTML = "";

  changed.forEach(item => {
    const div = document.createElement("div");
    div.className = "search-item";
    div.onclick = () => loadDiff(item.root, item.path);

    const title = document.createElement("div");
    title.className = "search-title";
    title.textContent = `${item.status}: ${item.root}:/${item.path}`;

    const meta = document.createElement("div");
    meta.className = "search-meta";
    meta.textContent = `snapshot: ${data.snapshot_created_at || "-"}`;

    div.appendChild(title);
    div.appendChild(meta);
    out.appendChild(div);
  });

  document.getElementById("diffOut").textContent = JSON.stringify(data, null, 2);
}

async function loadDiff(root, path) {
  const out = document.getElementById("diffOut");
  const title = document.getElementById("diffTitle");
  title.textContent = `Diff: ${root}:/${path}`;
  const data = await jsonFetch(`/api/diff?root=${encodeURIComponent(root)}&path=${encodeURIComponent(path)}`);
  out.textContent = data.diff || data.error || JSON.stringify(data, null, 2);
}
// TITAN_SEARCH_DIFF_JS_END
'''

if "TITAN_SEARCH_DIFF_JS_START" not in text:
    text = text.replace("</script>", js + "\n</script>", 1)

routes = r'''
@app.route("/api/search")
def api_search():
    from agent_core.search_diff import search_files
    return safe(lambda: search_files(request.args.get("q", ""), request.args.get("root", "all")))


@app.route("/api/snapshot", methods=["POST"])
def api_snapshot():
    from agent_core.search_diff import make_snapshot
    return safe(lambda: make_snapshot(request.json.get("root", "workspace")))


@app.route("/api/changed")
def api_changed():
    from agent_core.search_diff import changed_files
    return safe(lambda: changed_files(request.args.get("root", "workspace")))


@app.route("/api/diff")
def api_diff():
    from agent_core.search_diff import diff_file
    return safe(lambda: {"diff": diff_file(request.args.get("root", "workspace"), request.args.get("path", ""))})

'''

if '@app.route("/api/search")' not in text:
    text = text.replace('\n\nif __name__ == "__main__":', "\n\n" + routes + '\nif __name__ == "__main__":')

path.write_text(text, encoding="utf-8")
print("Patched dashboard search/diff.")
PY

python3 patch_dashboard_search_diff.py

echo "[4/4] Verifying..."

python3 -m py_compile agent_core/search_diff.py titan_terminal.py control_panel.py

cat > docs/PHASE13_SEARCH_DIFF.md <<EOF
# Phase 13 Search and Diff

Timestamp: $STAMP

Added:
- agent_core/search_diff.py
- dashboard Search / Diff tab
- terminal commands:
  - /search <query>
  - /snapshot [root]
  - /changed [root]
  - /diff <root> <path>

Dashboard APIs:
- GET /api/search
- POST /api/snapshot
- GET /api/changed
- GET /api/diff

Next:
- product templates
- git integration
- command palette
EOF

echo "Phase 13 complete."
