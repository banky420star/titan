#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
cd "$BASE"

mkdir -p docs backups logs jobs/running jobs/done jobs/cancelled jobs/logs jobs/traces products skills memory/project memory/user rag/docs rag/db

STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "backups/phase9_$STAMP"

cp control_panel.py "backups/phase9_$STAMP/control_panel.py" 2>/dev/null || true

cat > control_panel.py <<'PY'
from flask import Flask, jsonify, render_template_string, request
from pathlib import Path
from datetime import datetime
import json
import os
import subprocess
import sys
import traceback

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
sys.path.insert(0, str(BASE))

JOBS = BASE / "jobs"
RUNNING = JOBS / "running"
DONE = JOBS / "done"
CANCELLED = JOBS / "cancelled"
LOGS = JOBS / "logs"
TRACES = JOBS / "traces"
PRODUCTS = BASE / "products"

for folder in [RUNNING, DONE, CANCELLED, LOGS, TRACES, PRODUCTS]:
    folder.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)


HTML = r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Titan</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {
      --bg: #111214;
      --bg2: #18191c;
      --panel: rgba(255,255,255,.045);
      --panel2: rgba(255,255,255,.075);
      --line: rgba(255,255,255,.09);
      --text: #f4f4f5;
      --muted: #a1a1aa;
      --yellow: #e8dd69;
      --orange: #e8ab43;
      --coral: #dd867b;
      --eye: #0f172a;
    }

    * { box-sizing: border-box; }

    html, body {
      margin: 0;
      height: 100%;
      overflow: hidden;
      background:
        radial-gradient(circle at 45% -20%, rgba(232,171,67,.14), transparent 34%),
        linear-gradient(180deg, var(--bg), var(--bg2));
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .app {
      height: 100vh;
      display: grid;
      grid-template-columns: 285px 1fr;
      overflow: hidden;
    }

    aside {
      height: 100vh;
      overflow-y: auto;
      background: #101113;
      border-right: 1px solid var(--line);
      padding: 20px 14px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 0 8px;
      font-size: 22px;
      font-weight: 850;
      letter-spacing: -.04em;
    }

    .mini {
      display: grid;
      grid-template-columns: repeat(3, 10px);
      align-items: end;
      gap: 0;
      height: 34px;
      filter: drop-shadow(0 8px 12px rgba(0,0,0,.25));
    }

    .bar {
      width: 10px;
      border-radius: 5px 5px 3px 3px;
      position: relative;
    }

    .bar.y { height: 22px; background: var(--yellow); }
    .bar.o { height: 34px; background: var(--orange); }
    .bar.r { height: 26px; background: var(--coral); }

    .bar.o::after,
    .bar.r::after {
      content: "";
      position: absolute;
      left: 2px;
      top: 11px;
      width: 6px;
      height: 8px;
      border-radius: 50%;
      background: var(--eye);
      box-shadow: 2px -1px 0 -1px white;
    }

    nav {
      display: grid;
      gap: 6px;
    }

    nav button {
      border: 0;
      color: #d4d4d8;
      background: transparent;
      text-align: left;
      border-radius: 14px;
      padding: 12px 13px;
      cursor: pointer;
      font-size: 15px;
      display: flex;
      align-items: center;
      gap: 10px;
      transition: background .14s ease, color .14s ease, transform .14s ease;
    }

    nav button:hover {
      background: rgba(255,255,255,.06);
      color: white;
    }

    nav button.active {
      background: rgba(255,255,255,.09);
      color: white;
    }

    nav button:active,
    .btn:active,
    .card:active {
      transform: scale(.985);
    }

    .side-footer {
      margin-top: auto;
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 18px;
      padding: 12px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
    }

    main {
      height: 100vh;
      overflow-y: auto;
      padding: 34px;
    }

    .shell {
      max-width: 1120px;
      margin: 0 auto;
    }

    .hero {
      display: grid;
      grid-template-columns: 150px 1fr;
      gap: 26px;
      align-items: center;
      margin-bottom: 22px;
    }

    .mascot-wrap {
      height: 150px;
      display: grid;
      place-items: center;
      position: relative;
    }

    .mascot-glow {
      position: absolute;
      width: 112px;
      height: 40px;
      bottom: 18px;
      background: rgba(232,171,67,.24);
      filter: blur(14px);
      border-radius: 50%;
    }

    .mascot {
      position: relative;
      width: 118px;
      height: 126px;
      image-rendering: pixelated;
      display: grid;
      place-items: center;
      animation: floaty 3.4s ease-in-out infinite;
      filter: drop-shadow(0 14px 24px rgba(0,0,0,.28));
    }

    @keyframes floaty {
      50% { transform: translateY(-7px); }
    }

    .sprite {
      display: grid;
      grid-template-columns: repeat(13, 8px);
      grid-auto-rows: 8px;
      gap: 0;
    }

    .px { width: 8px; height: 8px; }
    .Y { background: var(--yellow); }
    .O { background: var(--orange); }
    .R { background: var(--coral); }
    .B { background: var(--eye); }
    .W { background: white; }

    h1 {
      margin: 0;
      font-size: 58px;
      letter-spacing: -.06em;
      line-height: 1;
    }

    .subtitle {
      margin-top: 10px;
      color: var(--muted);
      font-size: 18px;
    }

    .composer {
      display: flex;
      gap: 10px;
      height: 62px;
      padding: 8px;
      background: rgba(255,255,255,.055);
      border: 1px solid var(--line);
      border-radius: 999px;
      margin-bottom: 16px;
      position: sticky;
      top: 16px;
      z-index: 10;
      backdrop-filter: blur(14px);
    }

    .composer input {
      flex: 1;
      min-width: 0;
      border: 0;
      outline: 0;
      background: transparent;
      color: white;
      padding: 0 14px;
      font-size: 16px;
    }

    .btn {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.075);
      color: white;
      border-radius: 999px;
      padding: 10px 14px;
      cursor: pointer;
      transition: background .14s ease, transform .14s ease;
    }

    .btn:hover {
      background: rgba(255,255,255,.11);
    }

    .btn.primary {
      min-width: 48px;
      background: rgba(232,171,67,.24);
      border-color: rgba(232,171,67,.26);
    }

    .view {
      display: none;
    }

    .view.active {
      display: block;
    }

    .panel {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 24px;
      overflow: hidden;
      margin-bottom: 18px;
    }

    .panel-head {
      padding: 15px 18px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }

    .panel-body {
      padding: 18px;
    }

    .messages {
      height: 390px;
      overflow-y: auto;
      display: grid;
      gap: 12px;
      padding: 18px;
    }

    .msg {
      max-width: 84%;
      padding: 13px 15px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.055);
      border-radius: 20px;
      white-space: pre-wrap;
      line-height: 1.45;
      word-break: break-word;
      animation: msgIn .16s ease both;
    }

    @keyframes msgIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .msg.user {
      justify-self: end;
      background: rgba(79,70,229,.18);
      border-color: rgba(124,140,255,.24);
    }

    .msg small {
      display: block;
      color: var(--muted);
      margin-bottom: 5px;
      font-weight: 700;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
    }

    .card {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 20px;
      padding: 16px;
      cursor: pointer;
      min-height: 118px;
      transition: background .14s ease, transform .14s ease;
    }

    .card:hover {
      background: var(--panel2);
      transform: translateY(-2px);
    }

    .card h3 {
      margin: 8px 0 6px;
      font-size: 16px;
    }

    .card p {
      margin: 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.38;
    }

    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 13px;
      line-height: 1.45;
      color: #e5e7eb;
    }

    .row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }

    .field {
      flex: 1;
      min-width: 240px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.06);
      border-radius: 14px;
      color: white;
      padding: 12px;
      outline: 0;
    }

    @media (max-width: 900px) {
      html, body { overflow: auto; }
      .app { display: block; height: auto; }
      aside { height: auto; }
      main { height: auto; padding: 20px; }
      .hero { grid-template-columns: 1fr; }
      .grid { grid-template-columns: 1fr; }
      .composer { position: static; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <div class="brand">
        <div class="mini">
          <div class="bar y"></div><div class="bar o"></div><div class="bar r"></div>
        </div>
        Titan
      </div>

      <nav>
        <button class="active" onclick="showView('chat', this)">💬 Chat</button>
        <button onclick="showView('jobs', this); loadJobs()">▣ Jobs</button>
        <button onclick="showView('skills', this); loadSkills()">✧ Skills</button>
        <button onclick="showView('memory', this); loadMemory()">🧠 Memory</button>
        <button onclick="showView('rag', this); loadRag()">⌕ RAG</button>
        <button onclick="showView('models', this); loadModels()">☷ Models</button>
        <button onclick="showView('permissions', this); loadMode()">⚙ Permissions</button>
      </nav>

      <div class="side-footer">
        Local Titan<br>
        Dashboard: 5050<br>
        Models: Ollama local
      </div>
    </aside>

    <main>
      <div class="shell">
        <section class="hero">
          <div class="mascot-wrap">
            <div class="mascot-glow"></div>
            <div class="mascot">
              <div class="sprite" id="sprite"></div>
            </div>
          </div>
          <div>
            <h1>Titan</h1>
            <div class="subtitle">Local agent dashboard. Chat, jobs, skills, memory, RAG, models, and permissions.</div>
          </div>
        </section>

        <section id="view-chat" class="view active">
          <form class="composer" onsubmit="sendChat(event)">
            <input id="chatInput" placeholder="Ask Titan..." autocomplete="off">
            <button class="btn primary" type="submit">↑</button>
          </form>

          <div class="panel">
            <div class="panel-head">
              <strong>Titan Chat</strong>
              <button class="btn" onclick="clearChat()">Clear</button>
            </div>
            <div class="messages" id="messages">
              <div class="msg"><small>Titan</small>Ready. Ask me to build, inspect, search, remember, index, or run jobs.</div>
            </div>
          </div>

          <div class="grid">
            <div class="card" onclick="quick('Show me the workspace tree.')"><div>🗂</div><h3>Workspace</h3><p>Inspect files and project structure.</p></div>
            <div class="card" onclick="quick('Search RAG for Titan dashboard port and summarize the result.')"><div>⌕</div><h3>RAG Search</h3><p>Use local knowledge.</p></div>
            <div class="card" onclick="quick('List my skills.')"><div>✧</div><h3>Skills</h3><p>Show reusable workflows.</p></div>
          </div>
        </section>

        <section id="view-jobs" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Jobs</strong>
              <button class="btn" onclick="loadJobs()">Refresh</button>
            </div>
            <div class="panel-body"><pre id="jobsOut">Loading...</pre></div>
          </div>
        </section>

        <section id="view-skills" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Skills</strong>
              <button class="btn" onclick="loadSkills()">Refresh</button>
            </div>
            <div class="panel-body">
              <div class="row">
                <input class="field" id="skillName" placeholder="skill name">
                <input class="field" id="skillDesc" placeholder="description">
                <button class="btn" onclick="createSkill()">Create</button>
              </div>
              <pre id="skillsOut">Loading...</pre>
            </div>
          </div>
        </section>

        <section id="view-memory" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Memory</strong>
              <button class="btn" onclick="loadMemory()">Refresh</button>
            </div>
            <div class="panel-body">
              <div class="row">
                <input class="field" id="memoryText" placeholder="memory to save">
                <button class="btn" onclick="saveMemory()">Remember</button>
              </div>
              <div class="row">
                <input class="field" id="memoryQuery" placeholder="search memories">
                <button class="btn" onclick="searchMemory()">Search</button>
              </div>
              <pre id="memoryOut">Loading...</pre>
            </div>
          </div>
        </section>

        <section id="view-rag" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>RAG</strong>
              <div>
                <button class="btn" onclick="loadRag()">Status</button>
                <button class="btn" onclick="indexRag()">Index</button>
              </div>
            </div>
            <div class="panel-body">
              <div class="row">
                <input class="field" id="ragQuery" placeholder="search RAG">
                <button class="btn" onclick="searchRag()">Search</button>
              </div>
              <pre id="ragOut">Loading...</pre>
            </div>
          </div>
        </section>

        <section id="view-models" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Models</strong>
              <button class="btn" onclick="loadModels()">Refresh</button>
            </div>
            <div class="panel-body">
              <div class="row">
                <button class="btn" onclick="setProfile('tiny')">Tiny</button>
                <button class="btn" onclick="setProfile('fast')">Fast</button>
                <button class="btn" onclick="setProfile('coder')">Coder</button>
                <button class="btn" onclick="setProfile('smart')">Smart</button>
                <button class="btn" onclick="setProfile('heavy')">Heavy</button>
                <button class="btn" onclick="setProfile('max')">Max</button>
              </div>
              <pre id="modelsOut">Loading...</pre>
            </div>
          </div>
        </section>

        <section id="view-permissions" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Permissions</strong>
              <button class="btn" onclick="loadMode()">Refresh</button>
            </div>
            <div class="panel-body">
              <div class="row">
                <button class="btn" onclick="setMode('safe')">Safe</button>
                <button class="btn" onclick="setMode('power')">Power</button>
                <button class="btn" onclick="setMode('agentic')">Agentic</button>
              </div>
              <div class="row">
                <input class="field" id="runCmd" placeholder="approved shell command">
                <button class="btn" onclick="runCommand()">Run</button>
              </div>
              <pre id="modeOut">Loading...</pre>
            </div>
          </div>
        </section>
      </div>
    </main>
  </div>

<script>
const spriteRows = [
  ".....OOOO.....",
  "....OOOOOO....",
  "..YYYOOOORRR..",
  ".YYYYOOOORRRR.",
  ".YYYYOBWORRBR.",
  ".YYYYOOOORRRR.",
  "..YYYOOOORRR..",
  "....OOOOOO...."
];

const colors = {
  "Y": "Y",
  "O": "O",
  "R": "R",
  "B": "B",
  "W": "W"
};

function drawSprite(blink=false) {
  const sprite = document.getElementById("sprite");
  sprite.innerHTML = "";
  const rows = blink ? [
    ".....OOOO.....",
    "....OOOOOO....",
    "..YYYOOOORRR..",
    ".YYYYOOOORRRR.",
    ".YYYYOBBORRBB.",
    ".YYYYOOOORRRR.",
    "..YYYOOOORRR..",
    "....OOOOOO...."
  ] : spriteRows;

  for (const row of rows) {
    for (const c of row) {
      const d = document.createElement("div");
      d.className = "px " + (colors[c] || "");
      sprite.appendChild(d);
    }
  }
}
drawSprite(false);
setInterval(() => {
  drawSprite(true);
  setTimeout(() => drawSprite(false), 140);
}, 30000);

function showView(name, btn) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  document.getElementById("view-" + name).classList.add("active");
  document.querySelectorAll("nav button").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");
}

function addMessage(role, text) {
  const box = document.getElementById("messages");
  const d = document.createElement("div");
  d.className = "msg " + (role === "user" ? "user" : "");
  d.innerHTML = "<small>" + (role === "user" ? "You" : "Titan") + "</small>";
  const body = document.createElement("div");
  body.textContent = typeof text === "string" ? text : JSON.stringify(text, null, 2);
  d.appendChild(body);
  box.appendChild(d);
  box.scrollTop = box.scrollHeight;
}

function clearChat() {
  document.getElementById("messages").innerHTML = "";
  addMessage("assistant", "Clean slate.");
}

async function jsonFetch(url, options={}) {
  const res = await fetch(url, options);
  return await res.json();
}

async function sendChat(event) {
  event.preventDefault();
  const input = document.getElementById("chatInput");
  const task = input.value.trim();
  if (!task) return;
  input.value = "";
  await quick(task);
}

async function quick(task) {
  addMessage("user", task);
  addMessage("assistant", "Started background job...");
  const data = await jsonFetch("/api/task", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({task})
  });
  if (data.error) {
    addMessage("assistant", data.error);
    return;
  }
  addMessage("assistant", "Job: " + data.job_id);
  pollJob(data.job_id);
}

async function pollJob(id) {
  for (let i = 0; i < 240; i++) {
    const data = await jsonFetch("/api/job/" + encodeURIComponent(id));
    if (data.status === "done" || data.status === "error" || data.status === "cancelled") {
      addMessage("assistant", data.result || data.error || JSON.stringify(data, null, 2));
      return;
    }
    await new Promise(r => setTimeout(r, 1500));
  }
  addMessage("assistant", "Job still running: " + id);
}

async function loadJobs() {
  document.getElementById("jobsOut").textContent = JSON.stringify(await jsonFetch("/api/jobs"), null, 2);
}

async function loadSkills() {
  document.getElementById("skillsOut").textContent = (await jsonFetch("/api/skills")).result;
}

async function createSkill() {
  const name = document.getElementById("skillName").value.trim();
  const description = document.getElementById("skillDesc").value.trim();
  document.getElementById("skillsOut").textContent = JSON.stringify(await jsonFetch("/api/skills/create", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({name, description})
  }), null, 2);
}

async function loadMemory() {
  document.getElementById("memoryOut").textContent = (await jsonFetch("/api/memory")).result;
}

async function saveMemory() {
  const text = document.getElementById("memoryText").value.trim();
  document.getElementById("memoryOut").textContent = JSON.stringify(await jsonFetch("/api/memory/save", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({text})
  }), null, 2);
}

async function searchMemory() {
  const q = document.getElementById("memoryQuery").value.trim();
  document.getElementById("memoryOut").textContent = (await jsonFetch("/api/memory/search?q=" + encodeURIComponent(q))).result;
}

async function loadRag() {
  document.getElementById("ragOut").textContent = (await jsonFetch("/api/rag")).result;
}

async function indexRag() {
  document.getElementById("ragOut").textContent = "Indexing...";
  document.getElementById("ragOut").textContent = JSON.stringify(await jsonFetch("/api/rag/index", {method:"POST"}), null, 2);
}

async function searchRag() {
  const q = document.getElementById("ragQuery").value.trim();
  document.getElementById("ragOut").textContent = (await jsonFetch("/api/rag/search?q=" + encodeURIComponent(q))).result;
}

async function loadModels() {
  document.getElementById("modelsOut").textContent = JSON.stringify(await jsonFetch("/api/models"), null, 2);
}

async function setProfile(profile) {
  document.getElementById("modelsOut").textContent = JSON.stringify(await jsonFetch("/api/models/profile", {
    method:"POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({profile})
  }), null, 2);
}

async function loadMode() {
  document.getElementById("modeOut").textContent = (await jsonFetch("/api/mode")).result;
}

async function setMode(mode) {
  document.getElementById("modeOut").textContent = JSON.stringify(await jsonFetch("/api/mode", {
    method:"POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({mode})
  }), null, 2);
}

async function runCommand() {
  const command = document.getElementById("runCmd").value.trim();
  document.getElementById("modeOut").textContent = JSON.stringify(await jsonFetch("/api/run", {
    method:"POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({command})
  }), null, 2);
}
</script>
</body>
</html>
"""


def safe(fn):
    try:
        return jsonify(fn())
    except Exception:
        return jsonify({"error": traceback.format_exc()}), 500


def now():
    return datetime.now().isoformat(timespec="seconds")


def make_job_id():
    count = len(list(RUNNING.glob("*.json"))) + len(list(DONE.glob("*.json"))) + 1
    return "dash-" + datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{count:03d}"


def start_job(task):
    job_id = make_job_id()
    job = {
        "id": job_id,
        "task": task,
        "status": "queued",
        "created_at": now(),
        "source": "dashboard",
        "max_steps": 8
    }

    (RUNNING / f"{job_id}.json").write_text(json.dumps(job, indent=2), encoding="utf-8")

    worker = BASE / "background_worker.py"
    subprocess.Popen(
        [sys.executable, str(worker), job_id],
        cwd=str(BASE),
        stdout=(LOGS / f"{job_id}.stdout.log").open("w"),
        stderr=(LOGS / f"{job_id}.stderr.log").open("w"),
        start_new_session=True
    )

    return {"job_id": job_id, "status": "queued"}


def read_job(job_id):
    for folder in [RUNNING, DONE]:
        path = folder / f"{job_id}.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            trace = TRACES / f"{job_id}.trace.md"
            log = LOGS / f"{job_id}.log"
            data["trace"] = trace.read_text(errors="ignore")[-8000:] if trace.exists() else ""
            data["log"] = log.read_text(errors="ignore")[-4000:] if log.exists() else ""
            return data
    return {"error": "Job not found", "job_id": job_id}


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/api/task", methods=["POST"])
def api_task():
    return safe(lambda: start_job(request.json.get("task", "").strip()))


@app.route("/api/job/<job_id>")
def api_job(job_id):
    return safe(lambda: read_job(job_id))


@app.route("/api/jobs")
def api_jobs():
    def run():
        jobs = []
        for folder in [RUNNING, DONE]:
            for p in sorted(folder.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:40]:
                try:
                    jobs.append(json.loads(p.read_text(encoding="utf-8")))
                except Exception:
                    pass
        return {"jobs": jobs}
    return safe(run)


@app.route("/api/skills")
def api_skills():
    from agent_core.skills import list_skills
    return safe(lambda: {"result": list_skills()})


@app.route("/api/skills/create", methods=["POST"])
def api_skill_create():
    from agent_core.skills import create_skill_pack
    return safe(lambda: {"result": create_skill_pack(request.json.get("name", ""), request.json.get("description", ""), [])})


@app.route("/api/memory")
def api_memory():
    from agent_core.memory import memory_list
    return safe(lambda: {"result": memory_list("all", 50)})


@app.route("/api/memory/save", methods=["POST"])
def api_memory_save():
    from agent_core.memory import memory_save
    return safe(lambda: {"result": memory_save(request.json.get("text", ""), "project_fact", "project", ["dashboard"])})


@app.route("/api/memory/search")
def api_memory_search():
    from agent_core.memory import memory_search
    return safe(lambda: {"result": memory_search(request.args.get("q", ""), "all", 8)})


@app.route("/api/rag")
def api_rag():
    from agent_core.rag import rag_status
    return safe(lambda: {"result": rag_status()})


@app.route("/api/rag/index", methods=["POST"])
def api_rag_index():
    from agent_core.rag import rag_index
    return safe(lambda: {"result": rag_index()})


@app.route("/api/rag/search")
def api_rag_search():
    from agent_core.rag import rag_search
    return safe(lambda: {"result": rag_search(request.args.get("q", ""), 5)})


@app.route("/api/models")
def api_models():
    def run():
        cfg = json.loads((BASE / "config.json").read_text(encoding="utf-8"))
        return {
            "active_profile": cfg.get("active_profile"),
            "model": cfg.get("model"),
            "fallback_model": cfg.get("fallback_model"),
            "role_models": cfg.get("role_models"),
            "profiles": cfg.get("model_profiles", {})
        }
    return safe(run)


@app.route("/api/models/profile", methods=["POST"])
def api_model_profile():
    def run():
        cfg_path = BASE / "config.json"
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        profile = request.json.get("profile", "")
        profiles = cfg.get("model_profiles", {})
        if profile not in profiles:
            return {"error": "Unknown profile", "available": list(profiles.keys())}
        cfg.update(profiles[profile])
        cfg["active_profile"] = profile
        cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        return {"result": "Profile enabled", "profile": profile, "model": cfg.get("model")}
    return safe(run)


@app.route("/api/mode", methods=["GET", "POST"])
def api_mode():
    from agent_core.approvals import permission_status, set_mode
    if request.method == "GET":
        return safe(lambda: {"result": permission_status()})
    return safe(lambda: {"result": set_mode(request.json.get("mode", ""))})


@app.route("/api/run", methods=["POST"])
def api_run():
    from agent_core.tools import run_command
    return safe(lambda: {"result": run_command(request.json.get("command", ""))})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
PY

python3 -m py_compile control_panel.py

cat > docs/PHASE9_DASHBOARD_INTEGRATION.md <<EOF
# Phase 9 Dashboard Integration

Timestamp: $STAMP

Rebuilt:
- control_panel.py

Dashboard views:
- Chat
- Jobs
- Skills
- Memory
- RAG
- Models
- Permissions

APIs:
- POST /api/task
- GET /api/job/<id>
- GET /api/jobs
- GET /api/skills
- POST /api/skills/create
- GET /api/memory
- POST /api/memory/save
- GET /api/memory/search
- GET /api/rag
- POST /api/rag/index
- GET /api/rag/search
- GET /api/models
- POST /api/models/profile
- GET/POST /api/mode
- POST /api/run

Next:
- dashboard visual polish
- live trace viewer
- approvals queue
- file browser
EOF

echo "Phase 9 complete."
