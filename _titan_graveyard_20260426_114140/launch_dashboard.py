from pathlib import Path
import os
import subprocess
import sys
import time
import urllib.request
import webbrowser

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
URL = "http://127.0.0.1:5050"

def is_running():
    try:
        with urllib.request.urlopen(URL, timeout=1.2) as response:
            return response.status == 200
    except Exception:
        return False

def main():
    dashboard = BASE / "control_panel_titan_ui.py"
    if not dashboard.exists():
        dashboard = BASE / "control_panel.py"

    if not dashboard.exists():
        print("ERROR: control_panel_titan_ui.py or control_panel.py not found.")
        return 1

    logs = BASE / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    stdout_log = logs / "dashboard_stdout.log"
    stderr_log = logs / "dashboard_stderr.log"

    if not is_running():
        env = os.environ.copy()
        env["FLASK_DEBUG"] = "0"

        subprocess.Popen(
            [sys.executable, str(dashboard)],
            cwd=str(BASE),
            env=env,
            stdout=stdout_log.open("a"),
            stderr=stderr_log.open("a"),
            start_new_session=True
        )

        time.sleep(1.4)

    webbrowser.open(URL)

    print("Dashboard launched.")
    print("URL:", URL)
    print("File:", dashboard)
    print("stdout:", stdout_log)
    print("stderr:", stderr_log)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
