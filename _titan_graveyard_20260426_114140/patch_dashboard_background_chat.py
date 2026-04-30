from pathlib import Path
import re

path = Path("control_panel_titan_ui.py")
if not path.exists():
    path = Path("control_panel.py")

if not path.exists():
    raise SystemExit("Could not find control_panel_titan_ui.py or control_panel.py")

text = path.read_text()

# Add imports.
if "import subprocess" not in text:
    text = text.replace("import traceback\n", "import traceback\nimport subprocess\n")
if "from datetime import datetime" not in text:
    text = text.replace("from pathlib import Path\n", "from pathlib import Path\nfrom datetime import datetime\n")

# Add helper functions before @app.route("/")
marker = '@app.route("/")'
if marker not in text:
    raise SystemExit('Could not find @app.route("/")')

helpers = r'''
def make_dashboard_job_id():
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    RUNNING_JOBS.mkdir(parents=True, exist_ok=True)
    DONE_JOBS.mkdir(parents=True, exist_ok=True)
    count = len(list(RUNNING_JOBS.glob("*.json"))) + len(list(DONE_JOBS.glob("*.json"))) + 1
    return f"dash-{stamp}-{count:03d}"


def start_dashboard_background_job(task):
    JOBS.mkdir(parents=True, exist_ok=True)
    RUNNING_JOBS.mkdir(parents=True, exist_ok=True)
    DONE_JOBS.mkdir(parents=True, exist_ok=True)
    (JOBS / "logs").mkdir(parents=True, exist_ok=True)

    job_id = make_dashboard_job_id()

    job = {
        "id": job_id,
        "task": task,
        "status": "queued",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "max_steps": 28,
        "source": "dashboard"
    }

    job_file = RUNNING_JOBS / f"{job_id}.json"
    job_file.write_text(json.dumps(job, indent=2), encoding="utf-8")

    log_file = JOBS / "logs" / f"{job_id}.log"
    log_file.write_text(f"[{job['created_at']}] Queued from dashboard: {task}\n", encoding="utf-8")

    worker = BASE / "background_worker.py"
    if not worker.exists():
        return {
            "error": "background_worker.py not found",
            "job_id": job_id
        }

    subprocess.Popen(
        [sys.executable, str(worker), job_id],
        cwd=str(BASE),
        stdout=(JOBS / "logs" / f"{job_id}.stdout.log").open("w"),
        stderr=(JOBS / "logs" / f"{job_id}.stderr.log").open("w"),
        start_new_session=True
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "message": f"Background job started: {job_id}"
    }


def read_dashboard_job(job_id):
    candidates = [
        RUNNING_JOBS / f"{job_id}.json",
        DONE_JOBS / f"{job_id}.json"
    ]

    job_path = next((p for p in candidates if p.exists()), None)

    if not job_path:
        return {
            "error": "Job not found",
            "job_id": job_id
        }

    data = json.loads(job_path.read_text(encoding="utf-8"))

    trace_path = JOBS / "logs" / f"{job_id}.trace.md"
    log_path = JOBS / "logs" / f"{job_id}.log"
    stderr_path = JOBS / "logs" / f"{job_id}.stderr.log"

    data["trace"] = trace_path.read_text(errors="ignore")[-8000:] if trace_path.exists() else ""
    data["log"] = log_path.read_text(errors="ignore")[-5000:] if log_path.exists() else ""
    data["stderr"] = stderr_path.read_text(errors="ignore")[-3000:] if stderr_path.exists() else ""

    return data

'''

if "def start_dashboard_background_job(" not in text:
    text = text.replace(marker, helpers + "\n" + marker)

# Replace /api/task route.
start = text.find('@app.route("/api/task", methods=["POST"])')
if start == -1:
    raise SystemExit("Could not find /api/task route")

end = text.find('\n\n@app.route(', start + 1)
if end == -1:
    raise SystemExit("Could not find end of /api/task route")

new_task_route = r'''@app.route("/api/task", methods=["POST"])
def api_task():
    def run():
        task = request.json.get("task", "").strip()
        if not task:
            return {"error": "Empty task"}

        return start_dashboard_background_job(task)

    return safe_json_response(run)


@app.route("/api/job/<job_id>")
def api_job(job_id):
    return safe_json_response(lambda: read_dashboard_job(job_id))
'''

text = text[:start] + new_task_route + text[end:]

path.write_text(text)
print(f"Patched dashboard backend for background chat jobs in {path}")
