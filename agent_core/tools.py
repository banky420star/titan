from pathlib import Path
import json
import re
import shlex
import subprocess
import sys
from agent_core.skills import create_skill_pack, list_skills, run_skill, install_dependency
from agent_core.rag import rag_status, rag_index, rag_search
from agent_core.memory import memory_save, memory_search, memory_list, memory_delete
from agent_core.web_tools import web_search, fetch_url, download_url

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
    from agent_core.approvals import validate_command, permission_status

    command = str(command or "").strip()

    ok, reason, parts = validate_command(command)

    if not ok:
        return (
            "Command blocked: " + reason + "\n\n"
            + permission_status()
        )

    try:
        r = subprocess.run(
            parts,
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=120
        )

        return compact(
            f"Command: {command}\n"
            f"Reason: {reason}\n"
            f"cwd: {WORKSPACE}\n"
            f"exit_code: {r.returncode}\n\n"
            f"stdout:\n{r.stdout}\n\n"
            f"stderr:\n{r.stderr}",
            12000
        )
    except Exception as e:
        return "Command failed safely: " + repr(e)


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

    if name == "list_skills":
        return list_skills()
    if name == "create_skill_pack":
        return create_skill_pack(inp.get("name", ""), inp.get("description", ""), inp.get("dependencies", []))
    if name == "run_skill":
        return run_skill(inp.get("name", ""), inp.get("task", ""), inp.get("context", ""))
    if name == "install_dependency":
        return install_dependency(inp.get("package", ""))

    if name == "rag_status":
        return rag_status()
    if name == "rag_index":
        return rag_index()
    if name == "rag_search":
        return rag_search(inp.get("query", ""), inp.get("top_k", 5))

    if name == "memory_save":
        return memory_save(inp.get("text", ""), inp.get("kind", "project_fact"), inp.get("scope", "project"), inp.get("tags", []))
    if name == "memory_search":
        return memory_search(inp.get("query", ""), inp.get("scope", "all"), inp.get("limit", 8))
    if name == "memory_list":
        return memory_list(inp.get("scope", "all"), inp.get("limit", 40))
    if name == "memory_delete":
        return memory_delete(inp.get("id", ""))

    if name == "web_search":
        return web_search(inp.get("query", ""), inp.get("max_results", 6))
    if name == "fetch_url":
        return fetch_url(inp.get("url", ""))
    if name == "download_url":
        return download_url(inp.get("url", ""), inp.get("filename", ""))

    return "Unknown tool: " + str(name)
