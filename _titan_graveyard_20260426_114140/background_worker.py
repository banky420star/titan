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
