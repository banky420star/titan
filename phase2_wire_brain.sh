#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
cd "$BASE"

mkdir -p agent_core workspace products jobs/running jobs/done jobs/cancelled jobs/logs jobs/traces logs backups

STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "backups/phase2_$STAMP"

for f in titan_terminal.py control_panel.py background_worker.py config.json; do
  if [ -f "$f" ]; then
    cp "$f" "backups/phase2_$STAMP/$f"
  fi
done

cat > agent_core/__init__.py <<'PY'
__all__ = ["agent", "models", "tools"]
PY

cat > agent_core/models.py <<'PY'
from pathlib import Path
import json
import os
import urllib.request

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
CONFIG_PATH = BASE / "config.json"


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def ollama_chat(messages, model=None, timeout=180):
    cfg = load_config()
    model = model or cfg.get("model", "qwen3:8b")
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_ctx": int(cfg.get("num_ctx", 8192))
        }
    }

    req = urllib.request.Request(
        host + "/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))

    return data.get("message", {}).get("content", "")


def safe_chat(messages, model=None, timeout=180):
    cfg = load_config()
    primary = model or cfg.get("model", "qwen3:8b")
    fallback = cfg.get("fallback_model", "qwen2.5-coder:7b")

    try:
        return ollama_chat(messages, model=primary, timeout=timeout)
    except Exception as primary_error:
        if fallback and fallback != primary:
            try:
                return ollama_chat(messages, model=fallback, timeout=min(timeout, 120))
            except Exception as fallback_error:
                return json.dumps({
                    "final": "Titan model call failed safely. Primary error: "
                    + repr(primary_error)
                    + " Fallback error: "
                    + repr(fallback_error)
                })

        return json.dumps({
            "final": "Titan model call failed safely. Error: " + repr(primary_error)
        })
PY

cat > agent_core/tools.py <<'PY'
from pathlib import Path
import json
import re
import shlex
import subprocess
import sys

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
WORKSPACE = BASE / "workspace"
PRODUCTS = BASE / "products"
DOWNLOADS = BASE / "downloads"
SKILLS = BASE / "skills"
CONFIG_PATH = BASE / "config.json"

for folder in [WORKSPACE, PRODUCTS, DOWNLOADS, SKILLS]:
    folder.mkdir(parents=True, exist_ok=True)


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def compact(text, limit=12000):
    text = str(text or "")
    if text.startswith("%PDF-") or "\x00" in text[:2000]:
        return "[BINARY_OR_PDF_SUPPRESSED]"
    if len(text) > limit:
        return text[:limit] + "\n\n[TRUNCATED]"
    return text


def slug(value):
    value = str(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    return value.strip("-") or "item"


def workspace_path(filename):
    rel = Path(str(filename or "").strip())
    if rel.is_absolute():
        raise ValueError("Use workspace-relative paths only.")
    target = (WORKSPACE / rel).resolve()
    if not str(target).startswith(str(WORKSPACE.resolve())):
        raise ValueError("Path escapes workspace.")
    return target


def workspace_tree(max_items=180):
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    lines = ["workspace/"]
    items = sorted(WORKSPACE.rglob("*"))[:int(max_items)]

    if not items:
        lines.append("  empty")
    else:
        for p in items:
            rel = p.relative_to(WORKSPACE)
            lines.append("  " + str(rel) + ("/" if p.is_dir() else ""))

    return "\n".join(lines)


def list_files():
    return json.dumps(
        [str(p.relative_to(WORKSPACE)) for p in sorted(WORKSPACE.rglob("*")) if p.is_file()],
        indent=2
    )


def read_file(filename):
    p = workspace_path(filename)
    if not p.exists():
        return "File not found: " + str(filename)
    if p.is_dir():
        return "Path is a directory: " + str(filename)
    return compact(p.read_text(encoding="utf-8", errors="ignore"))


def write_file(filename, content):
    p = workspace_path(filename)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(str(content or ""), encoding="utf-8")
    return "Wrote file: " + str(p)


def append_file(filename, content):
    p = workspace_path(filename)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(str(content or ""))
    return "Appended file: " + str(p)


def list_products():
    PRODUCTS.mkdir(parents=True, exist_ok=True)
    items = [str(p) for p in sorted(PRODUCTS.iterdir()) if p.is_dir()]
    return "\n".join(items) if items else "No products found."


def create_product(name, kind="python_cli", description=""):
    name = slug(name)
    kind = str(kind or "python_cli").lower().strip()
    root = PRODUCTS / name
    root.mkdir(parents=True, exist_ok=True)

    if kind in ["flask", "flask_app"]:
        files = {
            "app.py": "from flask import Flask\n\napp = Flask(__name__)\n\n@app.route('/')\ndef home():\n    return '<h1>Titan product online</h1>'\n\n@app.route('/health')\ndef health():\n    return {'status': 'ok'}\n\nif __name__ == '__main__':\n    app.run(port=5055, debug=True)\n",
            "requirements.txt": "flask\n",
            "README.md": f"# {name}\n\n{description}\n\nRun:\n```bash\npip install -r requirements.txt\npython3 app.py\n```\n",
        }
    elif kind in ["static", "static_website"]:
        files = {
            "index.html": "<!doctype html><html><head><title>Titan Product</title><link rel='stylesheet' href='style.css'></head><body><main><h1>Titan product online</h1></main></body></html>\n",
            "style.css": "body{margin:0;min-height:100vh;display:grid;place-items:center;background:#111214;color:white;font-family:system-ui}\n",
            "README.md": f"# {name}\n\n{description}\n",
        }
    else:
        files = {
            "main.py": "def main():\n    print('Titan product online')\n\nif __name__ == '__main__':\n    main()\n",
            "requirements.txt": "",
            "README.md": f"# {name}\n\n{description}\n\nRun:\n```bash\npython3 main.py\n```\n",
        }

    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")

    return "Created product: " + str(root)


def run_command(command):
    cfg = load_config()
    allowed = cfg.get("allowed_command_prefixes", [
        "python",
        "python3",
        "pip",
        "ls",
        "pwd",
        "cat",
        "find",
        "grep",
        "mkdir",
        "touch",
        "pytest",
        "node",
        "npm",
        "git"
    ])

    command = str(command or "").strip()
    if not command:
        return "No command provided."

    try:
        parts = shlex.split(command)
    except Exception as e:
        return "Could not parse command: " + repr(e)

    if not parts:
        return "No command provided."

    if parts[0] not in allowed:
        return "Blocked command prefix: " + parts[0]

    try:
        r = subprocess.run(
            parts,
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=60
        )
        return compact(
            f"exit_code: {r.returncode}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}",
            12000
        )
    except Exception as e:
        return "Command failed: " + repr(e)


def dispatch_tool(name, inp):
    inp = inp or {}

    if name == "workspace_tree":
        return workspace_tree(inp.get("max_items", 180))
    if name == "list_files":
        return list_files()
    if name == "read_file":
        return read_file(inp.get("filename", ""))
    if name == "write_file":
        return write_file(inp.get("filename", ""), inp.get("content", ""))
    if name == "append_file":
        return append_file(inp.get("filename", ""), inp.get("content", ""))
    if name == "create_product":
        return create_product(inp.get("name", ""), inp.get("kind", "python_cli"), inp.get("description", ""))
    if name == "list_products":
        return list_products()
    if name == "run_command":
        return run_command(inp.get("command", ""))

    return "Unknown tool: " + str(name)
PY

cat > agent_core/agent.py <<'PY'
import json
import re
from agent_core.models import safe_chat
from agent_core.tools import dispatch_tool, compact


SYSTEM = """You are Titan, a local-first terminal coding and workspace agent.

You MUST respond with exactly one JSON object.

Tool call format:
{"tool":"tool_name","input":{...}}

Final answer format:
{"final":"short useful answer"}

Available tools:
- workspace_tree {"max_items":180}
- list_files {}
- read_file {"filename":"path"}
- write_file {"filename":"path","content":"text"}
- append_file {"filename":"path","content":"text"}
- run_command {"command":"python3 file.py"}
- create_product {"name":"demo","kind":"python_cli|flask_app|static_website","description":"text"}
- list_products {}

Rules:
- Inspect before editing.
- Use workspace-relative paths for file tools.
- Do not claim you used a tool unless tool output was provided.
- Keep output concise.
"""


def extract_json(text):
    text = str(text or "").strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.S)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return None

    return None


def run_agent(task, max_steps=8):
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": str(task)}
    ]

    for step in range(1, int(max_steps) + 1):
        raw = safe_chat(messages)
        obj = extract_json(raw)

        if not obj:
            return "The model returned prose instead of JSON:\n\n" + compact(raw, 4000)

        if "final" in obj:
            return str(obj.get("final", ""))

        if "tool" in obj:
            name = obj.get("tool")
            inp = obj.get("input") or {}

            result = dispatch_tool(name, inp)
            result = compact(result)

            messages.append({"role": "assistant", "content": json.dumps(obj)})
            messages.append({
                "role": "user",
                "content": "Tool result for " + str(name) + ":\n" + result
            })
            continue

        return "Invalid JSON object from model:\n" + json.dumps(obj, indent=2)

    return "Stopped after max steps without final answer."
PY

cat > background_worker.py <<'PY'
from pathlib import Path
from datetime import datetime
import json
import sys
import traceback

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
from agent_core.agent import run_agent


def now():
    return datetime.now().isoformat(timespec="seconds")


def log(job_id, text):
    with (LOGS / f"{job_id}.log").open("a", encoding="utf-8") as f:
        f.write(f"[{now()}] {text}\n")


def trace(job_id, title, text):
    with (TRACES / f"{job_id}.trace.md").open("a", encoding="utf-8") as f:
        f.write(f"\n\n## {title}\n\n{text}\n")


def run_job(job_id):
    path = RUNNING / f"{job_id}.json"
    if not path.exists():
        raise SystemExit("Job file missing: " + str(path))

    job = json.loads(path.read_text(encoding="utf-8"))
    job["status"] = "running"
    job["started_at"] = now()
    path.write_text(json.dumps(job, indent=2), encoding="utf-8")

    log(job_id, "Job started.")
    trace(job_id, "Task", job.get("task", ""))

    try:
        result = run_agent(job.get("task", ""), max_steps=int(job.get("max_steps", 8)))
        job["status"] = "done"
        job["result"] = str(result)
        trace(job_id, "Result", str(result))
        log(job_id, "Job completed.")
    except Exception:
        job["status"] = "error"
        job["result"] = traceback.format_exc()
        trace(job_id, "Error", job["result"])
        log(job_id, "Job failed.")

    job["finished_at"] = now()
    (DONE / f"{job_id}.json").write_text(json.dumps(job, indent=2), encoding="utf-8")
    path.unlink(missing_ok=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python3 background_worker.py <job_id>")
    run_job(sys.argv[1])
PY

python3 - <<'PY'
from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text()

if "def run_titan_prompt(" not in text:
    marker = "def repl():"
    if marker not in text:
        raise SystemExit("Could not find def repl()")

    helper = r'''
def run_titan_prompt(command):
    try:
        from agent_core.agent import run_agent
        return run_agent(command, max_steps=8)
    except Exception as e:
        return "Titan brain failed safely: " + repr(e)

'''
    text = text.replace(marker, helper + "\n" + marker)

old = '''            say_panel(
                "Clean-reset mode received:\\n\\n"
                + command
                + "\\n\\nNext build step will reconnect Ollama agent execution.",
                title="Titan",
                style="magenta"
            )
'''

new = '''            result = run_titan_prompt(command)
            say_panel(result, title="Titan", style="magenta")
'''

if old in text:
    text = text.replace(old, new)
else:
    # Fallback: replace the literal clean reset phrase if present.
    text = text.replace(
        'say_panel(\\n                "Clean-reset mode received:',
        'result = run_titan_prompt(command)\\n            say_panel(result, title="Titan", style="magenta")\\n            # old clean reset prompt disabled\\n            # say_panel(\\n                "Clean-reset mode received:'
    )

# Replace bg_job and jobs block if present.
start = text.find("def bg_job(")
end = text.find("\ndef repl():", start)

if start != -1 and end != -1:
    new_jobs = r'''def bg_job(task):
    jobs_dir = BASE / "jobs"
    running = jobs_dir / "running"
    logs = jobs_dir / "logs"
    running.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    job_id = "term-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    job = {
        "id": job_id,
        "task": task,
        "status": "queued",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source": "terminal",
        "max_steps": 8
    }

    (running / f"{job_id}.json").write_text(json.dumps(job, indent=2), encoding="utf-8")

    worker = BASE / "background_worker.py"
    subprocess.Popen(
        [sys.executable, str(worker), job_id],
        cwd=str(BASE),
        stdout=(logs / f"{job_id}.stdout.log").open("w"),
        stderr=(logs / f"{job_id}.stderr.log").open("w"),
        start_new_session=True
    )

    say_panel(
        f"Started background job: {job_id}\\n\\nUse /jobs or /job {job_id}",
        title="Background Job",
        style="green"
    )


def jobs():
    rows = []
    for folder_name in ["running", "done", "cancelled"]:
        folder = BASE / "jobs" / folder_name
        folder.mkdir(parents=True, exist_ok=True)

        for p in sorted(folder.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                rows.append(f"{data.get('id', p.stem)} | {data.get('status', folder_name)} | {data.get('task', '')[:120]}")
            except Exception as e:
                rows.append(f"{p.name} | unreadable | {e!r}")

    say_panel("\\n".join(rows) if rows else "No jobs found.", title="Jobs", style="cyan")


def show_job(job_id):
    job_id = str(job_id).strip()
    for folder_name in ["running", "done"]:
        p = BASE / "jobs" / folder_name / f"{job_id}.json"
        if p.exists():
            body = p.read_text(encoding="utf-8")
            say_panel(body[-12000:], title=f"Job: {job_id}", style="cyan")
            return
    say_panel("Job not found: " + job_id, title="Job", style="yellow")


def show_trace(job_id):
    job_id = str(job_id).strip()
    p = BASE / "jobs" / "traces" / f"{job_id}.trace.md"
    if p.exists():
        say_panel(p.read_text(errors="ignore")[-12000:], title=f"Trace: {job_id}", style="yellow")
    else:
        say_panel("Trace not found: " + job_id, title="Trace", style="yellow")

'''
    text = text[:start] + new_jobs + text[end:]

# Add /job and /trace-job handlers after /jobs.
if 'lower.startswith("/job ")' not in text:
    text = text.replace(
        '''            if lower == "/jobs":
                jobs()
                continue
''',
        '''            if lower == "/jobs":
                jobs()
                continue

            if lower.startswith("/job "):
                show_job(command.replace("/job ", "", 1).strip())
                continue

            if lower.startswith("/trace-job "):
                show_trace(command.replace("/trace-job ", "", 1).strip())
                continue
'''
    )

path.write_text(text)
print("Patched terminal to use agent_core and real background worker.")
PY

python3 - <<'PY'
from pathlib import Path

path = Path("control_panel.py")
text = path.read_text()

if "from agent_core.agent import run_agent" not in text:
    text = text.replace("import os\n", "import os\nimport sys\nsys.path.insert(0, str(BASE))\nfrom agent_core.agent import run_agent\n")

old = '''@app.route("/api/chat", methods=["POST"])
def chat():
    msg = request.json.get("message", "")
    return jsonify({
        "reply": "Clean reset mode received: " + msg,
        "next": "Next step is wiring Ollama agent execution into this clean shell."
    })
'''

new = '''@app.route("/api/chat", methods=["POST"])
def chat():
    msg = request.json.get("message", "")
    try:
        result = run_agent(msg, max_steps=8)
        return jsonify({"reply": result})
    except Exception as e:
        return jsonify({"error": repr(e)})
'''

if old in text:
    text = text.replace(old, new)

path.write_text(text)
print("Patched dashboard chat to use agent_core.")
PY

python3 -m py_compile agent_core/models.py agent_core/tools.py agent_core/agent.py titan_terminal.py background_worker.py control_panel.py

cat > docs/PHASE2_BRAIN_WIRED.md <<EOF
# Phase 2 Brain Wired

Timestamp: $STAMP

Added:
- agent_core/models.py
- agent_core/tools.py
- agent_core/agent.py
- background_worker.py

Patched:
- titan_terminal.py uses agent_core for plain prompts
- /bg launches real background worker
- /job and /trace-job added
- control_panel.py chat calls agent_core

Next:
- add subagents
- add skills
- add RAG
- improve dashboard background polling
EOF

echo "Phase 2 complete."
