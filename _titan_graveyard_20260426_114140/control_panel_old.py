from flask import Flask, jsonify, request, render_template_string
from pathlib import Path
import json
import sys

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
WORKSPACE = BASE / "workspace"
LOG_FILE = BASE / "logs" / "agent_v3.log"
SKILLS_DIR = BASE / "skills"

sys.path.insert(0, str(BASE))

import agent_v3

app = Flask(__name__)

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Titan Control Panel</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {
      --bg: #070914;
      --panel: rgba(18,24,42,.86);
      --line: rgba(148,163,184,.22);
      --text: #f8fafc;
      --muted: #a7b0c5;
      --blue: #38bdf8;
      --pink: #ec4899;
      --green: #22c55e;
      --amber: #f59e0b;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 15% 5%, rgba(56,189,248,.22), transparent 32%),
        radial-gradient(circle at 90% 15%, rgba(236,72,153,.18), transparent 34%),
        linear-gradient(135deg, #050714, #111827 50%, #160f2e);
      color: var(--text);
    }

    .shell {
      width: min(1300px, calc(100% - 28px));
      margin: 0 auto;
      padding: 28px 0;
    }

    .hero {
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: center;
      padding: 24px;
      border: 1px solid var(--line);
      border-radius: 28px;
      background: rgba(15,23,42,.82);
      box-shadow: 0 24px 80px rgba(0,0,0,.35);
      backdrop-filter: blur(16px);
    }

    .brand { display: flex; align-items: center; gap: 16px; }

    .brand img {
      width: 64px;
      height: 64px;
      border-radius: 20px;
      border: 1px solid var(--line);
      background: #111827;
    }

    h1 { margin: 0; font-size: clamp(32px, 5vw, 58px); letter-spacing: -.06em; }
    .sub { color: var(--muted); margin: 6px 0 0; }

    .pill {
      display: inline-flex;
      padding: 9px 13px;
      border: 1px solid rgba(34,197,94,.42);
      border-radius: 999px;
      color: #bbf7d0;
      background: rgba(22,163,74,.1);
      font-weight: 800;
    }

    .grid {
      display: grid;
      grid-template-columns: 1.2fr .8fr;
      gap: 18px;
      margin-top: 18px;
    }

    .panel {
      border: 1px solid var(--line);
      border-radius: 24px;
      background: var(--panel);
      padding: 20px;
      box-shadow: 0 18px 55px rgba(0,0,0,.25);
    }

    .panel h2 { margin: 0 0 14px; }

    textarea, input {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: rgba(2,6,23,.72);
      color: var(--text);
      padding: 14px;
      font: 15px/1.5 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      outline: none;
    }

    textarea { min-height: 150px; resize: vertical; }

    button {
      border: 0;
      border-radius: 14px;
      padding: 12px 16px;
      color: white;
      font-weight: 850;
      cursor: pointer;
      background: linear-gradient(135deg, var(--blue), var(--pink));
      box-shadow: 0 12px 30px rgba(56,189,248,.2);
    }

    button.secondary {
      background: rgba(148,163,184,.16);
      border: 1px solid var(--line);
      box-shadow: none;
    }

    .row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }

    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 520px;
      overflow: auto;
      color: #a7f3d0;
      background: rgba(2,6,23,.72);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      font: 13px/1.55 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }

    .cards {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 14px;
    }

    .card {
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 16px;
      background: rgba(255,255,255,.045);
    }

    .card strong { display: block; margin-bottom: 6px; }
    .card span { color: var(--muted); font-size: 14px; }

    @media (max-width: 900px) {
      .grid { grid-template-columns: 1fr; }
      .hero { align-items: flex-start; flex-direction: column; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="brand">
        <img src="/icon" alt="Titan icon">
        <div>
          <h1>Titan Control Panel</h1>
          <p class="sub">Local agent dashboard: workspace, skills, RAG, web search, logs, and task execution.</p>
        </div>
      </div>
      <span class="pill">● Local Online</span>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Agent Task</h2>
        <textarea id="task" placeholder="Ask Titan to build, inspect, edit, search, index, or run something..."></textarea>
        <div class="row">
          <button onclick="runTask()">Run Titan</button>
          <button class="secondary" onclick="tree()">Workspace Tree</button>
          <button class="secondary" onclick="skills()">Skills</button>
          <button class="secondary" onclick="logs()">Logs</button>
        </div>
        <h2 style="margin-top:18px;">Output</h2>
        <pre id="output">Ready.</pre>
      </div>

      <div class="panel">
        <h2>Quick Actions</h2>
        <div class="cards">
          <div class="card"><strong>🗂 Workspace</strong><span>Inspect and manage local projects.</span></div>
          <div class="card"><strong>🧩 Skills</strong><span>Load reusable workflows.</span></div>
          <div class="card"><strong>🧠 RAG</strong><span>Index and search local docs.</span></div>
          <div class="card"><strong>🌐 Web</strong><span>Search the web from Titan.</span></div>
          <div class="card"><strong>👥 Subagents</strong><span>Planner, coder, tester, reviewer.</span></div>
          <div class="card"><strong>🔐 Privilege</strong><span>Approval-gated commands.</span></div>
        </div>

        <h2 style="margin-top:18px;">RAG Search</h2>
        <input id="ragq" placeholder="Search local RAG memory...">
        <div class="row">
          <button class="secondary" onclick="indexRag()">Index Docs</button>
          <button class="secondary" onclick="ragSearch()">Search RAG</button>
        </div>

        <h2 style="margin-top:18px;">Web Search</h2>
        <input id="webq" placeholder="Search web...">
        <div class="row">
          <button class="secondary" onclick="webSearch()">Search Web</button>
        </div>
      </div>
    </section>
  </main>

<script>
const out = document.getElementById("output");

function show(x) {
  if (typeof x === "string") out.textContent = x;
  else out.textContent = JSON.stringify(x, null, 2);
}

async function post(url, data={}) {
  out.textContent = "Working...";
  const res = await fetch(url, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(data)
  });
  show(await res.json());
}

async function get(url) {
  out.textContent = "Working...";
  const res = await fetch(url);
  show(await res.json());
}

function runTask() {
  post("/api/task", {task: document.getElementById("task").value});
}

function tree() { get("/api/tree"); }
function skills() { get("/api/skills"); }
function logs() { get("/api/logs"); }
function indexRag() { post("/api/rag/index"); }
function ragSearch() { post("/api/rag/search", {query: document.getElementById("ragq").value}); }
function webSearch() { post("/api/web/search", {query: document.getElementById("webq").value}); }
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/icon")
def icon():
    return (BASE / "assets" / "titan_pixel_diva.svg").read_text(), 200, {"Content-Type": "image/svg+xml"}

@app.route("/api/task", methods=["POST"])
def api_task():
    task = request.json.get("task", "")
    if not task.strip():
        return jsonify({"error": "Empty task"})
    result = agent_v3.run_agent(task)
    return jsonify({"result": result})

@app.route("/api/tree")
def api_tree():
    return jsonify({"tree": agent_v3.tree()})

@app.route("/api/skills")
def api_skills():
    return jsonify({"skills": agent_v3.list_skills()})

@app.route("/api/logs")
def api_logs():
    if not LOG_FILE.exists():
      return jsonify({"logs": "No logs yet."})
    return jsonify({"logs": LOG_FILE.read_text(errors="ignore")[-12000:]})

@app.route("/api/rag/index", methods=["POST"])
def api_rag_index():
    return jsonify({"result": agent_v3.index_rag()})

@app.route("/api/rag/search", methods=["POST"])
def api_rag_search():
    query = request.json.get("query", "")
    return jsonify({"result": agent_v3.rag_search(query)})

@app.route("/api/web/search", methods=["POST"])
def api_web_search():
    query = request.json.get("query", "")
    return jsonify({"result": agent_v3.web_search(query)})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)
