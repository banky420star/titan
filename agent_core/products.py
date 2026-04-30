from pathlib import Path
from datetime import datetime
import json
import os
import re
import signal
import socket
import subprocess
import sys

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
PRODUCTS = BASE / "products"
LOGS = BASE / "logs" / "products"

PRODUCTS.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)


def slug(value):
    value = str(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    return value.strip("-") or "product"


def product_path(name):
    name = slug(name)
    root = (PRODUCTS / name).resolve()

    if not str(root).startswith(str(PRODUCTS.resolve())):
        raise ValueError("Invalid product path.")

    return root


def runtime_path(name):
    return product_path(name) / ".titan_runtime.json"


def pid_alive(pid):
    try:
        pid = int(pid)
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", int(port))) == 0


def find_free_port(start=5060, end=5099):
    for port in range(start, end + 1):
        if not port_open(port):
            return port
    raise RuntimeError("No free product port found in range 5060-5099.")


def detect_kind(root):
    if (root / "app.py").exists():
        return "flask_app"
    if (root / "index.html").exists():
        return "static_website"
    if (root / "main.py").exists():
        return "python_cli"
    return "unknown"


def read_runtime(name):
    path = runtime_path(name)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_runtime(name, data):
    path = runtime_path(name)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def create_product(name, kind="python_cli", description=""):
    try:
        from agent_core.product_templates import build_product, template_names
        if str(kind or "python_cli").strip() in template_names():
            return json.dumps(build_product(name, kind, description), indent=2)
    except Exception:
        pass

    from agent_core.tools import create_product as tool_create_product
    return tool_create_product(name, kind, description)


def list_product_templates():
    from agent_core.product_templates import list_templates
    return list_templates()


def list_products():
    rows = []

    for root in sorted(PRODUCTS.iterdir()):
        if not root.is_dir():
            continue

        kind = detect_kind(root)
        runtime = read_runtime(root.name)
        pid = runtime.get("pid")
        running = pid_alive(pid) if pid else False

        rows.append({
            "name": root.name,
            "path": str(root),
            "kind": kind,
            "running": running,
            "pid": pid if running else None,
            "url": runtime.get("url") if running else runtime.get("url"),
            "started_at": runtime.get("started_at"),
            "stdout": runtime.get("stdout"),
            "stderr": runtime.get("stderr")
        })

    return rows


def list_products_text():
    rows = list_products()

    if not rows:
        return "No products found."

    lines = []

    for item in rows:
        status = "running" if item["running"] else "stopped"
        lines.append(
            f"{item['name']} | {item['kind']} | {status}\n"
            f"  path: {item['path']}\n"
            f"  url: {item.get('url') or '-'}"
        )

    return "\n\n".join(lines)


def start_product(name):
    name = slug(name)
    root = product_path(name)

    if not root.exists():
        return {"error": "Product not found: " + name}

    runtime = read_runtime(name)
    old_pid = runtime.get("pid")

    if old_pid and pid_alive(old_pid):
        return {
            "result": "already running",
            "name": name,
            "pid": old_pid,
            "url": runtime.get("url")
        }

    kind = detect_kind(root)
    port = find_free_port()
    stdout_path = LOGS / f"{name}.stdout.log"
    stderr_path = LOGS / f"{name}.stderr.log"

    env = os.environ.copy()
    env["PORT"] = str(port)
    env["FLASK_RUN_PORT"] = str(port)

    if kind == "flask_app":
        cmd = [sys.executable, "app.py"]
        url = f"http://127.0.0.1:{port}"

        # Patch common generated Flask app if it hardcoded 5055.
        app_path = root / "app.py"
        try:
            app_text = app_path.read_text(encoding="utf-8")
            if "port=5055" in app_text and "os.environ" not in app_text:
                app_text = app_text.replace("from flask import Flask", "import os\nfrom flask import Flask")
                app_text = app_text.replace("app.run(port=5055, debug=True)", "app.run(port=int(os.environ.get('PORT', 5055)), debug=True)")
                app_path.write_text(app_text, encoding="utf-8")
        except Exception:
            pass

    elif kind == "static_website":
        cmd = [sys.executable, "-m", "http.server", str(port)]
        url = f"http://127.0.0.1:{port}"

    elif kind == "python_cli":
        cmd = [sys.executable, "main.py"]
        url = None

    else:
        return {"error": "Cannot start unknown product kind."}

    process = subprocess.Popen(
        cmd,
        cwd=str(root),
        env=env,
        stdout=stdout_path.open("a"),
        stderr=stderr_path.open("a"),
        start_new_session=True
    )

    data = {
        "name": name,
        "kind": kind,
        "pid": process.pid,
        "cmd": cmd,
        "url": url,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "stdout": str(stdout_path),
        "stderr": str(stderr_path)
    }

    write_runtime(name, data)

    return {
        "result": "started",
        **data
    }


def stop_product(name):
    name = slug(name)
    runtime = read_runtime(name)
    pid = runtime.get("pid")

    if not pid:
        return {"result": "not running", "name": name}

    if not pid_alive(pid):
        runtime["pid"] = None
        runtime["stopped_at"] = datetime.now().isoformat(timespec="seconds")
        write_runtime(name, runtime)
        return {"result": "already stopped", "name": name}

    try:
        os.killpg(int(pid), signal.SIGTERM)
    except Exception:
        try:
            os.kill(int(pid), signal.SIGTERM)
        except Exception as e:
            return {"error": "Failed to stop product: " + repr(e)}

    runtime["pid"] = None
    runtime["stopped_at"] = datetime.now().isoformat(timespec="seconds")
    write_runtime(name, runtime)

    return {"result": "stopped", "name": name}


def product_logs(name, limit=8000):
    name = slug(name)
    runtime = read_runtime(name)

    stdout = Path(runtime.get("stdout", LOGS / f"{name}.stdout.log"))
    stderr = Path(runtime.get("stderr", LOGS / f"{name}.stderr.log"))

    return {
        "stdout": stdout.read_text(errors="ignore")[-limit:] if stdout.exists() else "",
        "stderr": stderr.read_text(errors="ignore")[-limit:] if stderr.exists() else ""
    }
