from pathlib import Path
import re

path = Path("titan_terminal.py")
text = path.read_text()

Path("backups").mkdir(exist_ok=True)
Path("backups/titan_terminal_before_bg_hard_intercept.py").write_text(text)

# Make sure basic imports exist.
needed_imports = []
for imp in ["import json", "import subprocess", "import sys", "from datetime import datetime", "from pathlib import Path"]:
    if imp not in text:
        needed_imports.append(imp)

if needed_imports:
    text = "\n".join(needed_imports) + "\n" + text

# Add helpers before repl().
if "TITAN_BG_JOB_HELPERS_V2" not in text:
    marker = "def repl():"
    if marker not in text:
        raise SystemExit("Could not find def repl()")

    helpers = r'''
# TITAN_BG_JOB_HELPERS_V2
def titan_jobs_base():
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


def titan_start_bg_job(task):
    base, jobs = titan_jobs_base()
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

    (running / f"{job_id}.json").write_text(json.dumps(job, indent=2), encoding="utf-8")

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
        f"/jobs\n"
        f"/job {job_id}\n"
        f"/trace-job {job_id}\n"
        f"/cancel {job_id}",
        title="Background Job",
        border_style="green"
    ))


def titan_show_jobs():
    base, jobs = titan_jobs_base()
    rows = []

    for folder_name in ["running", "done"]:
        folder = jobs / folder_name
        for p in sorted(folder.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:25]:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                rows.append(
                    f"{data.get('id', p.stem)} | {data.get('status', folder_name)} | {data.get('created_at', '')}\n"
                    f"  {str(data.get('task', ''))[:160]}"
                )
            except Exception as e:
                rows.append(f"{p.name} | unreadable | {repr(e)}")

    console.print(Panel(
        "\n\n".join(rows) if rows else "No jobs found.",
        title="Jobs",
        border_style="cyan"
    ))


def titan_show_job(job_id):
    job_id = str(job_id).strip()
    base, jobs = titan_jobs_base()

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


def titan_show_trace(job_id):
    job_id = str(job_id).strip()
    base, jobs = titan_jobs_base()

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


def titan_cancel_job(job_id):
    job_id = str(job_id).strip()
    base, jobs = titan_jobs_base()

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

# Insert hard intercept right after command/user_input assignment inside repl.
if "TITAN_BG_HARD_INTERCEPT_V2" not in text:
    m = re.search(r"def repl\(\):", text)
    if not m:
        raise SystemExit("Could not find def repl()")

    start = m.end()
    next_def = text.find("\ndef ", start)
    if next_def == -1:
        next_def = len(text)

    repl_body = text[start:next_def]
    lines = repl_body.splitlines(True)

    insert_index = None

    # Find the first assignment to command or user_input inside repl.
    for i, line in enumerate(lines):
        if re.search(r"\b(command|user_input)\s*=", line):
            insert_index = i + 1
            break

    if insert_index is None:
        raise SystemExit("Could not find command/user_input assignment inside repl()")

    patch = r'''        # TITAN_BG_HARD_INTERCEPT_V2
        _cmd_raw = str(command if "command" in locals() else user_input).strip()

        if _cmd_raw.startswith("/bg "):
            try:
                titan_start_bg_job(_cmd_raw.replace("/bg ", "", 1).strip())
            except Exception as _e:
                console.print(Panel(
                    "Background job command failed but Titan stayed alive.\n\n" + repr(_e),
                    title="Background Job Error",
                    border_style="red"
                ))
            continue

        if _cmd_raw == "/jobs":
            try:
                titan_show_jobs()
            except Exception as _e:
                console.print(Panel(
                    "Jobs command failed but Titan stayed alive.\n\n" + repr(_e),
                    title="Jobs Error",
                    border_style="red"
                ))
            continue

        if _cmd_raw.startswith("/job "):
            try:
                titan_show_job(_cmd_raw.replace("/job ", "", 1).strip())
            except Exception as _e:
                console.print(Panel(
                    "Job command failed but Titan stayed alive.\n\n" + repr(_e),
                    title="Job Error",
                    border_style="red"
                ))
            continue

        if _cmd_raw.startswith("/trace-job "):
            try:
                titan_show_trace(_cmd_raw.replace("/trace-job ", "", 1).strip())
            except Exception as _e:
                console.print(Panel(
                    "Trace command failed but Titan stayed alive.\n\n" + repr(_e),
                    title="Trace Error",
                    border_style="red"
                ))
            continue

        if _cmd_raw.startswith("/cancel "):
            try:
                titan_cancel_job(_cmd_raw.replace("/cancel ", "", 1).strip())
            except Exception as _e:
                console.print(Panel(
                    "Cancel command failed but Titan stayed alive.\n\n" + repr(_e),
                    title="Cancel Error",
                    border_style="red"
                ))
            continue

'''

    lines.insert(insert_index, patch)
    text = text[:start] + "".join(lines) + text[next_def:]

path.write_text(text)
print("Installed hard /bg /jobs /job /trace-job /cancel intercept.")
