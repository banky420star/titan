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
