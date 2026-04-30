#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
cd "$BASE"

if [ -d "venv" ]; then
  source venv/bin/activate
fi

STAMP="$(date +%Y%m%d_%H%M%S)"

echo "[1/10] Creating folders..."
mkdir -p backups docs old_ui_archive logs downloads products
mkdir -p jobs/running jobs/done jobs/cancelled jobs/logs jobs/traces
mkdir -p skills subagents rag/docs rag/db

echo "[2/10] Backing up core files..."
mkdir -p "backups/sprint1_$STAMP"

for f in titan_terminal.py agent_v3.py control_panel.py control_panel_titan_ui.py config.json background_worker.py; do
  if [ -f "$f" ]; then
    cp "$f" "backups/sprint1_$STAMP/$f"
  fi
done

echo "[3/10] Killing old and new dashboard ports..."
lsof -ti :5000 | xargs kill -9 2>/dev/null || true
lsof -ti :5050 | xargs kill -9 2>/dev/null || true

echo "[4/10] Archiving old workspace UI if present..."
if [ -d "workspace/titan_control_panel" ]; then
  mv "workspace/titan_control_panel" "old_ui_archive/titan_control_panel_old_$STAMP"
  echo "Archived old UI to old_ui_archive/titan_control_panel_old_$STAMP"
else
  echo "No old workspace/titan_control_panel folder found."
fi

echo "[5/10] Writing background_worker.py..."
cat > background_worker.py <<'PY'
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
JOBS = BASE / "jobs"
RUNNING = JOBS / "running"
DONE = JOBS / "done"
CANCELLED = JOBS / "cancelled"
LOGS = JOBS / "logs"
TRACES = JOBS / "traces"

for folder in [RUNNING, DONE, CANCELLED, LOGS, TRACES]:
    folder.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BASE))
import agent_v3


def now():
    return datetime.now().isoformat(timespec="seconds")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def append_log(job_id, message):
    with (LOGS / f"{job_id}.log").open("a", encoding="utf-8") as f:
        f.write(f"[{now()}] {message}\n")


def append_trace(job_id, title, content):
    trace_path = TRACES / f"{job_id}.trace.md"
    with trace_path.open("a", encoding="utf-8") as f:
        f.write(f"\n\n## {title}\n\n")
        f.write(str(content))
        f.write("\n")


def compact(value, limit=8000):
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n[TRUNCATED]"


def is_cancelled(job_id):
    return (CANCELLED / f"{job_id}.cancel").exists()


def run_job(job_id):
    running_path = RUNNING / f"{job_id}.json"

    if not running_path.exists():
        raise SystemExit(f"Job file not found: {running_path}")

    job = read_json(running_path)
    task = job.get("task", "")

    job["status"] = "running"
    job["started_at"] = now()
    write_json(running_path, job)

    append_log(job_id, "Job started.")
    append_trace(job_id, "Task", task)

    try:
        if is_cancelled(job_id):
            job["status"] = "cancelled"
            job["result"] = "Cancelled before execution."
            append_log(job_id, "Cancelled before execution.")
        else:
            safe_task = (
                "BACKGROUND TITAN JOB. Complete this safely and practically. "
                "Use tools when useful. Do not wait for interactive approval in the background. "
                "If approval is required, record it and continue safe alternatives. "
                "Task: " + task
            )

            result = agent_v3.run_agent(
                safe_task,
                max_steps=int(job.get("max_steps", 12))
            )

            if is_cancelled(job_id):
                job["status"] = "cancelled"
                job["result"] = "Cancelled after partial execution.\n\n" + compact(result)
                append_log(job_id, "Cancelled after partial execution.")
            else:
                job["status"] = "done"
                job["result"] = compact(result)
                append_trace(job_id, "Final Result", compact(result))
                append_log(job_id, "Job completed.")

    except Exception:
        job["status"] = "error"
        job["error"] = traceback.format_exc()
        job["result"] = job["error"]
        append_trace(job_id, "Error", job["error"])
        append_log(job_id, "Job failed.")

    job["finished_at"] = now()
    write_json(DONE / f"{job_id}.json", job)
    running_path.unlink(missing_ok=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python3 background_worker.py <job_id>")
    run_job(sys.argv[1])
PY

echo "[6/10] Writing clean ChatGPT-style dashboard on port 5050..."
cat > control_panel_titan_ui.py <<'PY'
from flask import Flask, jsonify, request, render_template_string
from pathlib import Path
from datetime import datetime
import json
import os
import subprocess
import sys
import traceback

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
JOBS = BASE / "jobs"
RUNNING_JOBS = JOBS / "running"
DONE_JOBS = JOBS / "done"
CANCELLED_JOBS = JOBS / "cancelled"
JOB_LOGS = JOBS / "logs"
JOB_TRACES = JOBS / "traces"
PRODUCTS = BASE / "products"

for folder in [RUNNING_JOBS, DONE_JOBS, CANCELLED_JOBS, JOB_LOGS, JOB_TRACES, PRODUCTS]:
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
      --bg: #151619;
      --panel: rgba(255,255,255,0.045);
      --panel2: rgba(255,255,255,0.07);
      --line: rgba(255,255,255,0.08);
      --text: #f4f4f5;
      --muted: #a1a1aa;
      --accent: #fb923c;
      --accent2: #fb7185;
    }

    * { box-sizing: border-box; }

    html, body {
      margin: 0;
      height: 100%;
      overflow: hidden;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 50% 0%, rgba(251,146,60,0.10), transparent 28%),
        linear-gradient(180deg, #101113, #18191c);
      color: var(--text);
    }

    .app {
      height: 100vh;
      display: grid;
      grid-template-columns: 290px 1fr;
      overflow: hidden;
      transition: grid-template-columns 180ms ease;
    }

    .app.sidebar-collapsed {
      grid-template-columns: 82px 1fr;
    }

    .sidebar {
      height: 100vh;
      overflow-y: auto;
      border-right: 1px solid var(--line);
      background: #111214;
      padding: 22px 16px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }

    .brand {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    .brand-left {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }

    .mini-titan {
      width: 36px;
      height: 36px;
      border-radius: 15px;
      position: relative;
      flex: 0 0 auto;
      background:
        radial-gradient(circle at 30% 20%, rgba(255,255,255,0.55), transparent 30%),
        linear-gradient(145deg, #ffe66d, #fb923c 55%, #fb7185);
      box-shadow: inset -5px -6px 10px rgba(0,0,0,0.18), 0 12px 22px rgba(0,0,0,0.25);
    }

    .mini-titan:before, .mini-titan:after {
      content: "";
      position: absolute;
      top: 13px;
      width: 5px;
      height: 8px;
      border-radius: 99px;
      background: #111827;
    }

    .mini-titan:before { left: 10px; }
    .mini-titan:after { right: 10px; }

    .brand-title {
      font-size: 21px;
      font-weight: 800;
      letter-spacing: -0.03em;
    }

    .collapse {
      border: 1px solid var(--line);
      background: var(--panel);
      color: white;
      width: 36px;
      height: 36px;
      border-radius: 14px;
      cursor: pointer;
    }

    .nav {
      display: grid;
      gap: 6px;
    }

    .nav button {
      border: 0;
      background: transparent;
      color: #c7c9d1;
      min-height: 42px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 0 12px;
      cursor: pointer;
      font-size: 15px;
      text-align: left;
      transition: background 140ms ease, transform 140ms ease, color 140ms ease;
    }

    .nav button:hover {
      background: rgba(255,255,255,0.06);
      color: white;
    }

    .nav button:active, .send:active, .quick-card:active {
      transform: scale(0.985);
    }

    .nav .active {
      background: rgba(255,255,255,0.08);
      color: white;
    }

    .app.sidebar-collapsed .brand-title,
    .app.sidebar-collapsed .nav-label,
    .app.sidebar-collapsed .user-meta {
      display: none;
    }

    .app.sidebar-collapsed .nav button {
      justify-content: center;
      padding: 0;
    }

    .user {
      margin-top: auto;
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 18px;
      padding: 12px;
      display: flex;
      gap: 10px;
      align-items: center;
    }

    .avatar {
      width: 38px;
      height: 38px;
      border-radius: 14px;
      background: linear-gradient(135deg, #4f46e5, #1d4ed8);
      display: grid;
      place-items: center;
      font-weight: 800;
    }

    .main {
      height: 100vh;
      overflow-y: auto;
      padding: 42px 42px 24px;
    }

    .shell {
      max-width: 980px;
      margin: 0 auto;
    }

    .hero {
      display: grid;
      grid-template-columns: 128px 1fr;
      gap: 24px;
      align-items: center;
      margin-bottom: 26px;
    }

    .mascot-stage {
      position: relative;
      height: 124px;
      display: grid;
      place-items: center;
    }

    .glow {
      position: absolute;
      bottom: 5px;
      width: 118px;
      height: 45px;
      border-radius: 50%;
      background: rgba(251,146,60,0.28);
      filter: blur(12px);
    }

    .titan {
      position: relative;
      width: 104px;
      height: 112px;
      animation: floaty 3s ease-in-out infinite;
      filter: drop-shadow(0 14px 22px rgba(0,0,0,0.3));
    }

    @keyframes floaty {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-6px); }
    }

    .antenna {
      position: absolute;
      left: 48px;
      top: 0;
      width: 8px;
      height: 20px;
      border-radius: 99px;
      background: #fbbf24;
    }

    .antenna:before {
      content: "";
      position: absolute;
      top: -7px;
      left: -3px;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: #fef3c7;
      box-shadow: 0 0 12px rgba(251,191,36,0.55);
    }

    .head {
      position: absolute;
      left: 14px;
      top: 18px;
      width: 76px;
      height: 72px;
      border-radius: 28px;
      background:
        radial-gradient(circle at 30% 20%, rgba(255,255,255,0.48), transparent 30%),
        linear-gradient(145deg, #ffe66d, #fb923c 50%, #fb7185);
      box-shadow: inset -8px -10px 15px rgba(0,0,0,0.16), inset 8px 9px 15px rgba(255,255,255,0.24);
      overflow: hidden;
    }

    .eye {
      position: absolute;
      top: 28px;
      width: 17px;
      height: 23px;
      border-radius: 99px;
      background: #111827;
      overflow: hidden;
    }

    .eye.left { left: 18px; }
    .eye.right { right: 18px; }

    .pupil {
      position: absolute;
      left: 6px;
      top: 6px;
      width: 5px;
      height: 7px;
      border-radius: 99px;
      background: white;
      transition: transform 70ms linear;
    }

    .lid {
      position: absolute;
      inset: 0;
      background: linear-gradient(145deg, #ffe66d, #fb923c 50%, #fb7185);
      transform: translateY(-110%);
      transition: transform 100ms ease;
    }

    .eye.blink .lid {
      transform: translateY(0);
    }

    .smile {
      position: absolute;
      left: 31px;
      top: 50px;
      width: 13px;
      height: 8px;
      border-bottom: 3px solid #7f1d1d;
      border-radius: 50%;
    }

    .body {
      position: absolute;
      left: 24px;
      top: 78px;
      width: 56px;
      height: 32px;
      border-radius: 18px 18px 24px 24px;
      background: linear-gradient(145deg, #ffb35c, #fb7185);
    }

    .titan[data-state="working"] { animation-duration: 0.9s; }
    .titan[data-state="happy"] { animation: happy 650ms ease 2; }
    .titan[data-state="error"] { animation: shake 220ms ease 3; }

    @keyframes happy {
      50% { transform: translateY(-11px) scale(1.04); }
    }

    @keyframes shake {
      25% { transform: translateX(-3px); }
      75% { transform: translateX(3px); }
    }

    h1 {
      margin: 0;
      font-size: 58px;
      letter-spacing: -0.055em;
      line-height: 1;
    }

    .subtitle {
      color: var(--muted);
      font-size: 18px;
      margin-top: 10px;
    }

    .composer {
      position: sticky;
      top: 14px;
      z-index: 10;
      display: flex;
      align-items: center;
      gap: 12px;
      height: 68px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.055);
      backdrop-filter: blur(14px);
      border-radius: 999px;
      padding: 0 13px 0 22px;
      margin-bottom: 18px;
    }

    .composer:focus-within {
      border-color: rgba(251,146,60,0.35);
      background: rgba(255,255,255,0.075);
    }

    .composer input {
      flex: 1;
      min-width: 0;
      border: 0;
      outline: 0;
      background: transparent;
      color: white;
      font-size: 18px;
    }

    .send {
      width: 46px;
      height: 46px;
      border: 0;
      border-radius: 50%;
      background: rgba(255,255,255,0.12);
      color: white;
      cursor: pointer;
      font-size: 22px;
    }

    .chat {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 24px;
      overflow: hidden;
      margin-bottom: 18px;
    }

    .chat-head {
      padding: 16px 18px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .chat-messages {
      max-height: 380px;
      overflow-y: auto;
      padding: 18px;
      display: grid;
      gap: 14px;
    }

    .row {
      display: flex;
      gap: 10px;
      align-items: flex-start;
      animation: in 160ms ease both;
    }

    .row.user {
      justify-content: flex-end;
    }

    @keyframes in {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .bubble {
      max-width: min(720px, 82%);
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.055);
      padding: 13px 15px;
      border-radius: 20px;
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.45;
    }

    .row.user .bubble {
      background: rgba(79,70,229,0.18);
      border-color: rgba(124,140,255,0.25);
    }

    .bubble small {
      display: block;
      color: var(--muted);
      margin-bottom: 4px;
      font-weight: 700;
    }

    .typing span {
      display: inline-block;
      width: 6px;
      height: 6px;
      margin-right: 4px;
      border-radius: 50%;
      background: #d4d4d8;
      animation: dot 900ms infinite ease-in-out;
    }

    .typing span:nth-child(2) { animation-delay: 120ms; }
    .typing span:nth-child(3) { animation-delay: 240ms; }

    @keyframes dot {
      50% { transform: translateY(-4px); opacity: 1; }
    }

    .cards {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 14px;
      margin-bottom: 18px;
    }

    .quick-card {
      min-height: 140px;
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 20px;
      padding: 18px;
      cursor: pointer;
      transition: transform 140ms ease, background 140ms ease;
    }

    .quick-card:hover {
      transform: translateY(-2px);
      background: var(--panel2);
    }

    .quick-card h3 {
      margin: 12px 0 6px;
      font-size: 16px;
    }

    .quick-card p {
      margin: 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.38;
    }

    .panel {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 22px;
      padding: 18px;
      color: var(--muted);
    }

    .tiny {
      border: 1px solid var(--line);
      background: var(--panel);
      color: white;
      border-radius: 999px;
      padding: 8px 12px;
      cursor: pointer;
    }

    @media (max-width: 900px) {
      html, body { overflow: auto; }
      .app { display: block; height: auto; }
      .sidebar { height: auto; }
      .main { height: auto; overflow: visible; padding: 24px 16px; }
      .hero { grid-template-columns: 1fr; }
      .cards { grid-template-columns: 1fr 1fr; }
      .composer { position: static; }
    }

    @media (max-width: 620px) {
      .cards { grid-template-columns: 1fr; }
      h1 { font-size: 44px; }
    }
  </style>
</head>
<body>
  <div class="app" id="app">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-left">
          <div class="mini-titan"></div>
          <div class="brand-title">Titan</div>
        </div>
        <button class="collapse" onclick="toggleSidebar()">≪</button>
      </div>

      <div class="nav">
        <button class="active" onclick="quick('Say hello and summarize what Titan can do. Do not edit files.')"><span>⌂</span><span class="nav-label">Chat</span></button>
        <button onclick="getProducts()"><span>◇</span><span class="nav-label">Products</span></button>
        <button onclick="getJobs()"><span>▣</span><span class="nav-label">Jobs</span></button>
        <button onclick="quick('List available local skills. Do not edit files.')"><span>✧</span><span class="nav-label">Skills</span></button>
        <button onclick="quick('Show current models and role model assignments. Do not edit files.')"><span>☷</span><span class="nav-label">Models</span></button>
        <button onclick="quick('Run a brief doctor check. Do not edit files.')"><span>⚙</span><span class="nav-label">Doctor</span></button>
      </div>

      <div class="user">
        <div class="avatar">B</div>
        <div class="user-meta">
          <strong>Bank</strong>
          <div style="color:var(--muted);font-size:13px;">Local Titan</div>
        </div>
      </div>
    </aside>

    <main class="main">
      <section class="shell">
        <div class="hero">
          <div class="mascot-stage">
            <div class="glow"></div>
            <div class="titan" id="titan" data-state="idle">
              <div class="antenna"></div>
              <div class="head">
                <div class="eye left"><span class="pupil"></span><span class="lid"></span></div>
                <div class="eye right"><span class="pupil"></span><span class="lid"></span></div>
                <div class="smile"></div>
              </div>
              <div class="body"></div>
            </div>
          </div>
          <div>
            <h1>Titan</h1>
            <div class="subtitle">Local autonomous terminal agent with background jobs, skills, and subagents.</div>
          </div>
        </div>

        <form class="composer" onsubmit="sendPrompt(event)">
          <span>✧</span>
          <input id="prompt" placeholder="Ask Titan anything..." autocomplete="off">
          <button class="send" type="submit">↑</button>
        </form>

        <section class="chat">
          <div class="chat-head">
            <strong>Titan Chat</strong>
            <button class="tiny" onclick="clearChat()">Clear</button>
          </div>
          <div class="chat-messages" id="messages">
            <div class="row assistant"><div class="bubble"><small>Titan</small>Ready. Ask me to build, inspect, fix, launch, or research.</div></div>
          </div>
        </section>

        <section class="cards">
          <div class="quick-card" onclick="quick('Inspect the workspace and summarize the project structure. Do not edit files.')">
            <div>🗂</div><h3>Inspect workspace</h3><p>Find files, read code, and map the project.</p>
          </div>
          <div class="quick-card" onclick="quick('Launch a background audit job for Titan. Do not edit files.')">
            <div>🤖</div><h3>Background agents</h3><p>Run longer tasks without freezing the UI.</p>
          </div>
          <div class="quick-card" onclick="quick('Create a product scaffold called dashboard-test as python_cli and verify it.')">
            <div>🧊</div><h3>Build products</h3><p>Scaffold tools, apps, and local projects.</p>
          </div>
          <div class="quick-card" onclick="quick('Create a skill pack called dashboard-helper. Do not install external packages.')">
            <div>⚡</div><h3>Create skills</h3><p>Generate reusable Titan skill packs.</p>
          </div>
        </section>

        <section class="panel" id="statusPanel">Activity and job status will appear in chat.</section>
      </section>
    </main>
  </div>

  <script>
    const app = document.getElementById("app");
    const titan = document.getElementById("titan");
    const prompt = document.getElementById("prompt");
    const messages = document.getElementById("messages");
    const pupils = document.querySelectorAll(".pupil");
    const eyes = document.querySelectorAll(".eye");

    function toggleSidebar() {
      app.classList.toggle("sidebar-collapsed");
      localStorage.setItem("titanSidebarCollapsed", app.classList.contains("sidebar-collapsed") ? "1" : "0");
    }

    if (localStorage.getItem("titanSidebarCollapsed") === "1") {
      app.classList.add("sidebar-collapsed");
    }

    function setTitan(state) {
      titan.dataset.state = state;
    }

    function resetTitan(ms = 1400) {
      setTimeout(() => setTitan("idle"), ms);
    }

    window.addEventListener("mousemove", (event) => {
      const rect = titan.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const angle = Math.atan2(event.clientY - cy, event.clientX - cx);
      const x = Math.cos(angle) * 4;
      const y = Math.sin(angle) * 4;
      pupils.forEach(p => p.style.transform = `translate(${x}px, ${y}px)`);
    });

    function blink() {
      eyes.forEach(e => e.classList.add("blink"));
      setTimeout(() => eyes.forEach(e => e.classList.remove("blink")), 120);
    }

    setInterval(() => {
      if (Math.random() > 0.35) blink();
    }, 2200);

    prompt.addEventListener("focus", () => setTitan("working"));
    prompt.addEventListener("blur", () => resetTitan(300));

    function addMessage(role, text) {
      const row = document.createElement("div");
      row.className = "row " + role;
      const bubble = document.createElement("div");
      bubble.className = "bubble";
      const who = role === "user" ? "You" : "Titan";
      bubble.innerHTML = "<small>" + who + "</small>";
      const body = document.createElement("div");
      body.textContent = typeof text === "string" ? text : JSON.stringify(text, null, 2);
      bubble.appendChild(body);
      row.appendChild(bubble);
      messages.appendChild(row);
      messages.scrollTop = messages.scrollHeight;
      return row;
    }

    function addTyping() {
      const row = document.createElement("div");
      row.className = "row assistant";
      row.id = "typing";
      const bubble = document.createElement("div");
      bubble.className = "bubble typing";
      bubble.innerHTML = "<small>Titan</small><span></span><span></span><span></span>";
      row.appendChild(bubble);
      messages.appendChild(row);
      messages.scrollTop = messages.scrollHeight;
    }

    function removeTyping() {
      const t = document.getElementById("typing");
      if (t) t.remove();
    }

    function clearChat() {
      messages.innerHTML = "";
      addMessage("assistant", "Clean slate. What should we build?");
      setTitan("happy");
      resetTitan();
    }

    function textOf(obj) {
      if (typeof obj === "string") return obj;
      if (obj.result) return String(obj.result);
      if (obj.message) return String(obj.message);
      return JSON.stringify(obj, null, 2);
    }

    function stateForTask(task) {
      const t = task.toLowerCase();
      if (t.includes("find") || t.includes("search") || t.includes("list")) return "working";
      if (t.includes("build") || t.includes("create") || t.includes("scaffold")) return "working";
      if (t.includes("fix") || t.includes("debug")) return "working";
      return "working";
    }

    async function pollJob(jobId) {
      for (let i = 0; i < 240; i++) {
        const res = await fetch("/api/job/" + encodeURIComponent(jobId));
        const job = await res.json();

        if (job.status === "done") {
          removeTyping();
          addMessage("assistant", job.result || "Done.");
          setTitan("happy");
          resetTitan();
          return;
        }

        if (job.status === "error") {
          removeTyping();
          addMessage("assistant", job.result || job.error || "Job failed.");
          setTitan("error");
          resetTitan(2200);
          return;
        }

        if (job.status === "cancelled") {
          removeTyping();
          addMessage("assistant", "Job cancelled: " + jobId);
          setTitan("error");
          resetTitan(1600);
          return;
        }

        await new Promise(resolve => setTimeout(resolve, 1500));
      }

      removeTyping();
      addMessage("assistant", "Job is still running: " + jobId);
    }

    async function sendTask(task) {
      addMessage("user", task);
      addTyping();
      setTitan(stateForTask(task));

      const res = await fetch("/api/task", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({task})
      });

      const json = await res.json();

      if (json.error) {
        removeTyping();
        addMessage("assistant", json);
        setTitan("error");
        resetTitan(2200);
        return;
      }

      if (json.job_id) {
        removeTyping();
        addMessage("assistant", "Started background job: " + json.job_id + "\nI will post the result here.");
        addTyping();
        pollJob(json.job_id);
        return;
      }

      removeTyping();
      addMessage("assistant", textOf(json));
      setTitan("happy");
      resetTitan();
    }

    function sendPrompt(event) {
      event.preventDefault();
      const task = prompt.value.trim();
      if (!task) return;
      prompt.value = "";
      sendTask(task);
    }

    function quick(task) {
      sendTask(task);
    }

    async function getProducts() {
      setTitan("working");
      const res = await fetch("/api/products");
      addMessage("assistant", await res.json());
      setTitan("happy");
      resetTitan();
    }

    async function getJobs() {
      setTitan("working");
      const res = await fetch("/api/jobs");
      addMessage("assistant", await res.json());
      setTitan("happy");
      resetTitan();
    }
  </script>
</body>
</html>
"""

def safe_response(fn):
    try:
        return jsonify(fn())
    except Exception:
        return jsonify({"error": traceback.format_exc()}), 500


def make_job_id():
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    count = len(list(RUNNING_JOBS.glob("*.json"))) + len(list(DONE_JOBS.glob("*.json"))) + 1
    return f"dash-{stamp}-{count:03d}"


def start_job(task):
    job_id = make_job_id()
    job = {
        "id": job_id,
        "task": task,
        "status": "queued",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "max_steps": 12,
        "source": "dashboard"
    }

    job_path = RUNNING_JOBS / f"{job_id}.json"
    job_path.write_text(json.dumps(job, indent=2), encoding="utf-8")

    worker = BASE / "background_worker.py"
    if not worker.exists():
        return {"error": "background_worker.py missing", "job_id": job_id}

    subprocess.Popen(
        [sys.executable, str(worker), job_id],
        cwd=str(BASE),
        stdout=(JOB_LOGS / f"{job_id}.stdout.log").open("w"),
        stderr=(JOB_LOGS / f"{job_id}.stderr.log").open("w"),
        start_new_session=True
    )

    return {"job_id": job_id, "status": "queued", "message": "Background job started: " + job_id}


def read_job(job_id):
    candidates = [
        RUNNING_JOBS / f"{job_id}.json",
        DONE_JOBS / f"{job_id}.json"
    ]

    path = next((p for p in candidates if p.exists()), None)
    if not path:
        return {"error": "Job not found", "job_id": job_id}

    data = json.loads(path.read_text(encoding="utf-8"))

    trace = JOB_TRACES / f"{job_id}.trace.md"
    log = JOB_LOGS / f"{job_id}.log"
    stderr = JOB_LOGS / f"{job_id}.stderr.log"

    data["trace"] = trace.read_text(errors="ignore")[-8000:] if trace.exists() else ""
    data["log"] = log.read_text(errors="ignore")[-4000:] if log.exists() else ""
    data["stderr"] = stderr.read_text(errors="ignore")[-4000:] if stderr.exists() else ""
    return data


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/api/task", methods=["POST"])
def api_task():
    def run():
        task = request.json.get("task", "").strip()
        if not task:
            return {"error": "Empty task"}
        return start_job(task)
    return safe_response(run)


@app.route("/api/job/<job_id>")
def api_job(job_id):
    return safe_response(lambda: read_job(job_id))


@app.route("/api/jobs")
def api_jobs():
    def run():
        jobs = []
        for folder in [RUNNING_JOBS, DONE_JOBS]:
            for p in sorted(folder.glob("*.json"))[-30:]:
                try:
                    jobs.append(json.loads(p.read_text(encoding="utf-8")))
                except Exception:
                    pass
        return {"jobs": jobs}
    return safe_response(run)


@app.route("/api/products")
def api_products():
    def run():
        PRODUCTS.mkdir(parents=True, exist_ok=True)
        return {"products": [str(p) for p in sorted(PRODUCTS.iterdir()) if p.is_dir()]}
    return safe_response(run)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=os.environ.get("FLASK_DEBUG") == "1")
PY

cp control_panel_titan_ui.py control_panel.py

echo "[7/10] Patching agent_v3.py tools and timeout safety..."
python3 - <<'PY'
from pathlib import Path

path = Path("agent_v3.py")
text = path.read_text()

if "import urllib.parse" not in text:
    text = text.replace("import uuid\n", "import uuid\nimport urllib.parse\n")

if "def install_dependency(" not in text:
    marker = "def tool(name, inp):"
    if marker not in text:
        raise SystemExit("Could not find def tool(name, inp): in agent_v3.py")

    code = r'''
BUILDER_DOWNLOADS = BASE / "downloads"
BUILDER_PRODUCTS = BASE / "products"
BUILDER_SKILLS = BASE / "skills"

for _builder_dir in [BUILDER_DOWNLOADS, BUILDER_PRODUCTS, BUILDER_SKILLS]:
    _builder_dir.mkdir(parents=True, exist_ok=True)


def builder_slug(value):
    value = str(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    return value.strip("-") or "item"


def install_dependency(package):
    package = str(package or "").strip()
    if not package:
        return "No package provided."

    if not re.match(r"^[A-Za-z0-9_.\-\[\],=<>~!]+$", package):
        return "Blocked: unsafe package name."

    cmd = [sys.executable, "-m", "pip", "install", "-U", package]

    try:
        r = subprocess.run(
            cmd,
            cwd=str(BASE),
            capture_output=True,
            text=True,
            timeout=240
        )
        return f"exit_code: {r.returncode}\nstdout:\n{r.stdout[-8000:]}\nstderr:\n{r.stderr[-8000:]}"
    except Exception as e:
        return "Dependency install failed: " + repr(e)


def download_url(url, filename=""):
    url = str(url or "").strip()
    if not url.startswith(("http://", "https://")):
        return "Blocked: URL must start with http:// or https://"

    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    allowed = CONFIG.get("approved_download_domains", [
        "github.com",
        "raw.githubusercontent.com",
        "huggingface.co",
        "pypi.org",
        "files.pythonhosted.org"
    ])

    if not any(host == d or host.endswith("." + d) for d in allowed):
        return "Blocked: domain is not approved: " + host

    guessed = Path(parsed.path).name or "downloaded-file"
    safe_name = builder_slug(filename or guessed)
    target = (BUILDER_DOWNLOADS / safe_name).resolve()

    if not str(target).startswith(str(BUILDER_DOWNLOADS.resolve())):
        return "Blocked: invalid target path."

    try:
        with requests.get(url, stream=True, timeout=60, headers={"User-Agent": "TitanAgent/1.0"}) as r:
            r.raise_for_status()
            total = 0
            max_bytes = 250_000_000

            with target.open("wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > max_bytes:
                        target.unlink(missing_ok=True)
                        return "Blocked: file too large."
                    f.write(chunk)

        return f"Downloaded to {target} ({total} bytes)."
    except Exception as e:
        return "Download failed: " + repr(e)


def create_skill_pack(name, description="", dependencies=None):
    name = builder_slug(name)
    dependencies = dependencies or []
    root = BUILDER_SKILLS / name
    root.mkdir(parents=True, exist_ok=True)
    (root / "scripts").mkdir(exist_ok=True)
    (root / "templates").mkdir(exist_ok=True)

    skill_md = f"""# {name}

{description or "Titan local skill."}

## When to use

Use this skill when the task matches: {name}

## Workflow

1. Inspect relevant files.
2. Plan the change.
3. Make the smallest useful edit.
4. Run verification.
5. Report exact changes.

## Dependencies

{chr(10).join("- " + str(x) for x in dependencies) if dependencies else "- none"}
"""

    meta = {
        "name": name,
        "description": description or "Titan local skill.",
        "dependencies": dependencies,
        "entry": "SKILL.md"
    }

    (root / "SKILL.md").write_text(skill_md, encoding="utf-8")
    (root / "skill.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return "Created skill pack: " + str(root)


def list_products():
    BUILDER_PRODUCTS.mkdir(parents=True, exist_ok=True)
    items = [str(p) for p in sorted(BUILDER_PRODUCTS.iterdir()) if p.is_dir()]
    return "\n".join(items) if items else "No products found."


def create_product(name, kind="python_cli", description=""):
    name = builder_slug(name)
    kind = str(kind or "python_cli").strip().lower()
    root = BUILDER_PRODUCTS / name
    root.mkdir(parents=True, exist_ok=True)

    if kind in ["flask", "flask_app", "flask-app", "webapp"]:
        (root / "templates").mkdir(exist_ok=True)
        (root / "static").mkdir(exist_ok=True)
        files = {
            "app.py": "from flask import Flask, render_template\n\napp = Flask(__name__)\n\n@app.route('/')\ndef home():\n    return render_template('index.html')\n\n@app.route('/health')\ndef health():\n    return {'status': 'ok'}\n\nif __name__ == '__main__':\n    app.run(debug=True, port=5055)\n",
            "requirements.txt": "flask\n",
            "templates/index.html": "<!doctype html>\n<html><head><meta charset='utf-8'><title>Titan Product</title><link rel='stylesheet' href='/static/style.css'></head><body><main><h1>Titan Product</h1><p>Online.</p></main></body></html>\n",
            "static/style.css": "body{margin:0;font-family:system-ui;background:#111214;color:white}main{max-width:860px;margin:80px auto;padding:32px;border-radius:24px;background:#1f2937}\n",
            "README.md": "# " + name + "\n\n" + description + "\n\nRun:\n  pip install -r requirements.txt\n  python3 app.py\n"
        }
    elif kind in ["static", "static_website", "static-website"]:
        files = {
            "index.html": "<!doctype html>\n<html><head><meta charset='utf-8'><title>Titan Product</title><link rel='stylesheet' href='style.css'></head><body><main><h1>Titan Product</h1><p>Static site online.</p></main></body></html>\n",
            "style.css": "body{margin:0;min-height:100vh;display:grid;place-items:center;background:#111214;color:white;font-family:system-ui}\n",
            "README.md": "# " + name + "\n\n" + description + "\n"
        }
    else:
        files = {
            "main.py": "def main():\n    print('Titan product scaffold online.')\n\nif __name__ == '__main__':\n    main()\n",
            "requirements.txt": "",
            "README.md": "# " + name + "\n\n" + description + "\n\nRun:\n  python3 main.py\n"
        }

    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    return "Created product scaffold: " + str(root)
'''
    text = text.replace(marker, code + "\n" + marker)

unknown = '    return f"Unknown tool: {name}"'
dispatch = '''    if name == "install_dependency": return install_dependency(inp.get("package") or "")
    if name == "download_url": return download_url(inp.get("url") or "", inp.get("filename") or "")
    if name == "create_skill_pack": return create_skill_pack(inp.get("name") or "", inp.get("description") or "", inp.get("dependencies") or [])
    if name == "create_product": return create_product(inp.get("name") or "", inp.get("kind") or "python_cli", inp.get("description") or "")
    if name == "list_products": return list_products()
'''

if unknown in text and 'if name == "install_dependency"' not in text:
    text = text.replace(unknown, dispatch + unknown)

start = text.find("def chat(messages):")
if start != -1 and "Model call failed safely" not in text[start:start+2500]:
    end = text.find("\ndef ", start + 1)
    if end != -1:
        new_chat = r'''def chat(messages):
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_ctx": int(CONFIG.get("num_ctx", 8192))
        }
    }

    try:
        r = requests.post(CHAT_URL, json=payload, timeout=int(CONFIG.get("model_timeout", 180)))
        r.raise_for_status()
        return r.json()["message"]["content"]
    except Exception as primary_error:
        fallback = CONFIG.get("fallback_model", "qwen2.5-coder:7b")

        if fallback and fallback != MODEL:
            try:
                payload["model"] = fallback
                r = requests.post(CHAT_URL, json=payload, timeout=int(CONFIG.get("fallback_timeout", 120)))
                r.raise_for_status()
                return r.json()["message"]["content"]
            except Exception as fallback_error:
                return json.dumps({
                    "final": "Model call failed safely. Titan did not crash. Primary error: "
                    + repr(primary_error)
                    + " Fallback error: "
                    + repr(fallback_error)
                })

        return json.dumps({
            "final": "Model call failed safely. Titan did not crash. Error: " + repr(primary_error)
        })

'''
        text = text[:start] + new_chat + text[end:]

if "def safe_tool_result(" not in text:
    marker = "def run_agent("
    if marker in text:
        helper = r'''
def safe_tool_result(result, limit=12000):
    text = str(result or "")
    sample = text[:2000]
    if text.startswith("%PDF-") or "/Type /Catalog" in sample or "\x00" in sample:
        return "[BINARY_OR_PDF_SUPPRESSED]"
    if len(text) > limit:
        return text[:limit] + "\n\n[TRUNCATED TOOL RESULT]"
    return text

'''
        text = text.replace(marker, helper + marker)

text = text.replace(
    'print("\\nTool result:\\n" + str(result))',
    'result = safe_tool_result(result)\n        print("\\nTool result:\\n" + str(result))'
)

path.write_text(text)
print("agent_v3.py patched")
PY

echo "[8/10] Patching titan_terminal.py dashboard launcher and crash shield..."
python3 - <<'PY'
from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text()

prepend = ""
for line in ["import os", "import sys", "import time", "import subprocess", "import webbrowser"]:
    if line not in text:
        prepend += line + "\n"

if "from pathlib import Path" not in text:
    prepend += "from pathlib import Path\n"

if prepend:
    text = prepend + text

marker = "def repl():"
if marker not in text:
    raise SystemExit("Could not find def repl() in titan_terminal.py")

helper = r'''
def safe_execute_command(label, fn, *args):
    try:
        return fn(*args)
    except Exception as e:
        try:
            logs = Path("/Volumes/AI_DRIVE/TitanAgent/logs")
            logs.mkdir(parents=True, exist_ok=True)
            with (logs / "terminal_errors.log").open("a", encoding="utf-8") as f:
                f.write(f"{label}: {repr(e)}\n")
        except Exception:
            pass

        console.print(Panel(
            "Command failed but Titan stayed alive.\n\n"
            f"Command: {label}\n"
            f"Error: {repr(e)}",
            title="Command Error",
            border_style="red"
        ))


def dashboard_is_running():
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:5050", timeout=1.2) as response:
            return response.status == 200
    except Exception:
        return False


def launch_dashboard():
    base = Path("/Volumes/AI_DRIVE/TitanAgent")
    dashboard_file = base / "control_panel_titan_ui.py"

    if not dashboard_file.exists():
        dashboard_file = base / "control_panel.py"

    if not dashboard_file.exists():
        console.print(Panel(
            "Could not find control_panel_titan_ui.py or control_panel.py",
            title="Dashboard",
            border_style="red"
        ))
        return

    if dashboard_is_running():
        webbrowser.open("http://127.0.0.1:5050")
        console.print(Panel(
            "Dashboard is already running.\n\nURL: http://127.0.0.1:5050",
            title="Dashboard",
            border_style="green"
        ))
        return

    logs = base / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    stdout_log = logs / "dashboard_stdout.log"
    stderr_log = logs / "dashboard_stderr.log"

    env = os.environ.copy()
    env["FLASK_DEBUG"] = "0"

    subprocess.Popen(
        [sys.executable, str(dashboard_file)],
        cwd=str(base),
        env=env,
        stdout=stdout_log.open("a"),
        stderr=stderr_log.open("a"),
        start_new_session=True
    )

    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:5050")

    console.print(Panel(
        "Dashboard launch requested.\n\n"
        "URL: http://127.0.0.1:5050\n"
        f"File: {dashboard_file}\n\n"
        f"stdout log: {stdout_log}\n"
        f"stderr log: {stderr_log}",
        title="Dashboard",
        border_style="green"
    ))

'''

if "def launch_dashboard(" not in text:
    text = text.replace(marker, helper + "\n" + marker)

handler = '''        # TITAN_DASHBOARD_ALIAS_HANDLER
        if command == "/dashboard" or command.lower().strip() in ["launch dashboard", "open dashboard", "start dashboard", "launch dash board", "open dash board"]:
            safe_execute_command("/dashboard", launch_dashboard)
            continue

'''

if "TITAN_DASHBOARD_ALIAS_HANDLER" not in text:
    if "        run_agent_task(command)" in text:
        text = text.replace("        run_agent_task(command)", handler + "        run_agent_task(command)", 1)
    elif "run_agent_task(command)" in text:
        text = text.replace("run_agent_task(command)", handler + "        run_agent_task(command)", 1)
    else:
        raise SystemExit("Could not find run_agent_task(command) insertion point")

if '"/dashboard"' not in text:
    text = text.replace('"/exit",', '"/dashboard",\n    "/exit",')

path.write_text(text)
print("titan_terminal.py patched")
PY

echo "[9/10] Ensuring ./titan launcher exists..."
cat > titan <<'SH2'
#!/usr/bin/env bash
cd /Volumes/AI_DRIVE/TitanAgent
if [ -d "venv" ]; then
  source venv/bin/activate
fi
python3 titan_terminal.py
SH2
chmod +x titan

echo "[10/10] Writing docs and running verification..."
cat > docs/SPRINT_1_TERMINAL_REPAIR.md <<EOF
# Sprint 1 Terminal Repair

Timestamp: $STAMP

Completed:
- Backed up core files to backups/sprint1_$STAMP
- Archived old workspace UI if present
- Rewrote dashboard on port 5050
- Copied control_panel_titan_ui.py to control_panel.py
- Created background_worker.py
- Patched agent_v3.py missing tools
- Patched titan_terminal.py dashboard launcher
- Added crash shield helper
- Ensured ./titan launcher exists

Next:
- Test /dashboard from Titan
- Test dashboard chat background job
- Continue with agent_core refactor after stable
EOF

python3 -m py_compile titan_terminal.py agent_v3.py control_panel_titan_ui.py control_panel.py background_worker.py

echo ""
echo "Core file check:"
python3 - <<'PY'
from pathlib import Path
for item in ["titan_terminal.py", "agent_v3.py", "control_panel_titan_ui.py", "control_panel.py", "background_worker.py", "titan"]:
    p = Path(item)
    print(item, "OK" if p.exists() else "MISSING")
PY

echo ""
echo "Old workspace app check:"
find workspace -maxdepth 3 -name app.py || true

echo ""
echo "Tool check:"
grep -n "def install_dependency" agent_v3.py || true
grep -n "def download_url" agent_v3.py || true
grep -n "def create_skill_pack" agent_v3.py || true
grep -n "def create_product" agent_v3.py || true
grep -n "def list_products" agent_v3.py || true

echo ""
echo "DONE."
echo "Now run:"
echo "  ./titan"
echo "Then inside Titan run:"
echo "  /dashboard"
