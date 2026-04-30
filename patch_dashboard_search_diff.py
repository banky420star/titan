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
