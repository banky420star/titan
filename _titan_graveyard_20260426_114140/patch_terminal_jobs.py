from pathlib import Path
import re

path = Path("titan_terminal.py")
text = path.read_text()

backup_dir = Path("backups")
backup_dir.mkdir(exist_ok=True)
(backup_dir / "titan_terminal_before_jobs_patch.py").write_text(text)

if "TITAN_TERMINAL_JOBS_HELPERS" not in text:
    marker = "def repl():"
    if marker not in text:
        raise SystemExit("Could not find def repl()")

    helpers = r'''
# TITAN_TERMINAL_JOBS_HELPERS
def _job_base():
    from pathlib import Path
    base = Path("/Volumes/AI_DRIVE/TitanAgent")
    jobs = base / "jobs"
    for folder in [
        jobs / "running",
        jobs / "done",
        jobs / "cancelled",
        jobs / "logs",
        jobs / "traces",
    ]:
        folder.mkdir(parents=True, exist_ok=True)
    return base, jobs


def _read_json_file(path):
    import json
    return json.loads(path.read_text(encoding="utf-8"))


def start_terminal_bg_job(task):
    import json
    import subprocess
    import sys
    from datetime import datetime

    base, jobs = _job_base()
    running = jobs / "running"
    logs = jobs / "logs"

    job_id = "term-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    job = {
        "id": job_id,
        "task": str(task),
        "status": "queued",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "max_steps": 12,
        "source": "terminal"
    }

    job_path = running / f"{job_id}.json"
    job_path.write_text(json.dumps(job, indent=2), encoding="utf-8")

    worker = base / "background_worker.py"
    if not worker.exists():
        console.print(Panel(
            "background_worker.py is missing. Create it before using /bg.",
            title="Background Job",
            border_style="red"
        ))
        return

    subprocess.Popen(
        [sys.executable, str(worker), job_id],
        cwd=str(base),
        stdout=(logs / f"{job_id}.stdout.log").open("w"),
        stderr=(logs / f"{job_id}.stderr.log").open("w"),
        start_new_session=True
    )

    console.print(Panel(
        f"Started background job: {job_id}\n\n"
        f"Task: {task}\n\n"
        f"Use:\n"
        f"/job {job_id}\n"
        f"/trace-job {job_id}\n"
        f"/jobs",
        title="Background Job",
        border_style="green"
    ))


def show_terminal_jobs():
    import json

    base, jobs = _job_base()
    running = jobs / "running"
    done = jobs / "done"

    rows = []

    for folder, label in [(running, "running"), (done, "done")]:
        for p in sorted(folder.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                rows.append(
                    f"{data.get('id', p.stem)} | {data.get('status', label)} | {data.get('created_at', '')}\n"
                    f"  {str(data.get('task', ''))[:150]}"
                )
            except Exception as e:
                rows.append(f"{p.name} | unreadable | {repr(e)}")

    body = "\n\n".join(rows) if rows else "No jobs found."
    console.print(Panel(body, title="Jobs", border_style="cyan"))


def show_terminal_job(job_id):
    import json

    job_id = str(job_id).strip()
    base, jobs = _job_base()

    candidates = [
        jobs / "running" / f"{job_id}.json",
        jobs / "done" / f"{job_id}.json",
    ]

    job_path = next((p for p in candidates if p.exists()), None)

    if not job_path:
        console.print(Panel(
            f"Job not found: {job_id}",
            title="Job",
            border_style="yellow"
        ))
        return

    data = json.loads(job_path.read_text(encoding="utf-8"))

    body = json.dumps(data, indent=2)
    if len(body) > 14000:
        body = body[:14000] + "\n\n[TRUNCATED]"

    console.print(Panel(body, title=f"Job: {job_id}", border_style="cyan"))


def show_terminal_job_trace(job_id):
    job_id = str(job_id).strip()
    base, jobs = _job_base()

    candidates = [
        jobs / "traces" / f"{job_id}.trace.md",
        jobs / "logs" / f"{job_id}.trace.md",
    ]

    trace_path = next((p for p in candidates if p.exists()), None)

    if not trace_path:
        console.print(Panel(
            f"No trace found for: {job_id}",
            title="Job Trace",
            border_style="yellow"
        ))
        return

    body = trace_path.read_text(errors="ignore")
    if len(body) > 16000:
        body = body[-16000:]

    console.print(Panel(body, title=f"Trace: {job_id}", border_style="yellow"))


def cancel_terminal_job(job_id):
    from datetime import datetime

    job_id = str(job_id).strip()
    base, jobs = _job_base()
    cancel_path = jobs / "cancelled" / f"{job_id}.cancel"
    cancel_path.write_text(
        "cancelled_at=" + datetime.now().isoformat(timespec="seconds"),
        encoding="utf-8"
    )

    console.print(Panel(
        f"Cancel signal written for: {job_id}",
        title="Cancel Job",
        border_style="yellow"
    ))

'''
    text = text.replace(marker, helpers + "\n" + marker)

if "TITAN_TERMINAL_JOB_HANDLERS" not in text:
    handler = r'''        # TITAN_TERMINAL_JOB_HANDLERS
        if str(command).strip().startswith("/bg "):
            start_terminal_bg_job(str(command).replace("/bg ", "", 1).strip())
            continue

        if str(command).strip() == "/jobs":
            show_terminal_jobs()
            continue

        if str(command).strip().startswith("/job "):
            show_terminal_job(str(command).replace("/job ", "", 1).strip())
            continue

        if str(command).strip().startswith("/trace-job "):
            show_terminal_job_trace(str(command).replace("/trace-job ", "", 1).strip())
            continue

        if str(command).strip().startswith("/cancel "):
            cancel_terminal_job(str(command).replace("/cancel ", "", 1).strip())
            continue

'''

    # Put this before the generic AI task execution.
    if "        run_agent_task(command)" in text:
        text = text.replace("        run_agent_task(command)", handler + "        run_agent_task(command)", 1)
    else:
        raise SystemExit("Could not find run_agent_task(command) insertion point")

path.write_text(text)
print("Patched terminal job commands.")
