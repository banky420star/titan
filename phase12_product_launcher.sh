#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
cd "$BASE"

mkdir -p agent_core products logs/products docs backups

STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "backups/phase12_$STAMP"

cp control_panel.py "backups/phase12_$STAMP/control_panel.py" 2>/dev/null || true
cp titan_terminal.py "backups/phase12_$STAMP/titan_terminal.py" 2>/dev/null || true
cp agent_core/tools.py "backups/phase12_$STAMP/tools.py" 2>/dev/null || true

echo "[1/4] Writing agent_core/products.py..."

cat > agent_core/products.py <<'PY'
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
    from agent_core.tools import create_product as tool_create_product
    return tool_create_product(name, kind, description)


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
PY

echo "[2/4] Patching titan_terminal.py..."

cat > patch_terminal_products.py <<'PY'
from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

if "def terminal_products(" not in text:
    marker = "def repl():"
    if marker not in text:
        raise SystemExit("Could not find def repl()")

    helpers = r'''
def terminal_products():
    try:
        from agent_core.products import list_products_text
        say_panel(list_products_text(), title="Products", style="cyan")
    except Exception as e:
        say_panel("Products failed: " + repr(e), title="Products", style="red")


def terminal_product_create(args):
    try:
        from agent_core.products import create_product

        parts = str(args or "").strip().split()
        if not parts:
            say_panel("Usage: /product-create <name> [python_cli|flask_app|static_website]", title="Products", style="yellow")
            return

        name = parts[0]
        kind = parts[1] if len(parts) > 1 else "python_cli"

        result = create_product(name, kind, "Created from Titan terminal.")
        say_panel(result, title="Product Created", style="green")
    except Exception as e:
        say_panel("Create product failed: " + repr(e), title="Products", style="red")


def terminal_product_start(name):
    try:
        from agent_core.products import start_product
        result = start_product(name)
        say_panel(json.dumps(result, indent=2), title="Product Start", style="green")
    except Exception as e:
        say_panel("Start product failed: " + repr(e), title="Products", style="red")


def terminal_product_stop(name):
    try:
        from agent_core.products import stop_product
        result = stop_product(name)
        say_panel(json.dumps(result, indent=2), title="Product Stop", style="yellow")
    except Exception as e:
        say_panel("Stop product failed: " + repr(e), title="Products", style="red")


def terminal_product_logs(name):
    try:
        from agent_core.products import product_logs
        result = product_logs(name)
        say_panel(json.dumps(result, indent=2), title="Product Logs", style="magenta")
    except Exception as e:
        say_panel("Product logs failed: " + repr(e), title="Products", style="red")


'''
    text = text.replace(marker, helpers + marker)

if 'lower == "/products"' not in text:
    target = '''            if lower == "/skills":
                show_skills()
                continue
'''
    replacement = '''            if lower == "/skills":
                show_skills()
                continue

            if lower == "/products":
                terminal_products()
                continue

            if lower.startswith("/product-create "):
                terminal_product_create(command.replace("/product-create ", "", 1).strip())
                continue

            if lower.startswith("/product-start "):
                terminal_product_start(command.replace("/product-start ", "", 1).strip())
                continue

            if lower.startswith("/product-stop "):
                terminal_product_stop(command.replace("/product-stop ", "", 1).strip())
                continue

            if lower.startswith("/product-logs "):
                terminal_product_logs(command.replace("/product-logs ", "", 1).strip())
                continue
'''

    if target not in text:
        target = '''            if lower == "/models":
                models()
                continue
'''
        replacement = target + '''
            if lower == "/products":
                terminal_products()
                continue

            if lower.startswith("/product-create "):
                terminal_product_create(command.replace("/product-create ", "", 1).strip())
                continue

            if lower.startswith("/product-start "):
                terminal_product_start(command.replace("/product-start ", "", 1).strip())
                continue

            if lower.startswith("/product-stop "):
                terminal_product_stop(command.replace("/product-stop ", "", 1).strip())
                continue

            if lower.startswith("/product-logs "):
                terminal_product_logs(command.replace("/product-logs ", "", 1).strip())
                continue
'''
    if target not in text:
        raise SystemExit("Could not find insertion point for product commands.")

    text = text.replace(target, replacement, 1)

text = text.replace(
    "/skills      Show Titan skills\n",
    "/skills      Show Titan skills\n/products    Show products\n/product-create <name> [kind]\n/product-start <name>\n/product-stop <name>\n/product-logs <name>\n"
)

path.write_text(text, encoding="utf-8")
print("Patched terminal product commands.")
PY

python3 patch_terminal_products.py

echo "[3/4] Patching dashboard Products tab..."

cat > patch_dashboard_products.py <<'PY'
from pathlib import Path
import re

path = Path("control_panel.py")
text = path.read_text(encoding="utf-8")

if "showView('products'" not in text:
    text = text.replace(
        '<button onclick="showView(\'files\', this); loadFiles()">🗂 Files</button>',
        '<button onclick="showView(\'files\', this); loadFiles()">🗂 Files</button>\n'
        '        <button onclick="showView(\'products\', this); loadProducts()">◇ Products</button>'
    )

if 'id="view-products"' not in text:
    section = r'''
        <section id="view-products" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Products</strong>
              <button class="btn" onclick="loadProducts()">Refresh</button>
            </div>

            <div class="panel-body">
              <div class="row">
                <input class="field" id="productName" placeholder="product name">
                <select class="field small-field" id="productKind">
                  <option value="python_cli">python_cli</option>
                  <option value="flask_app">flask_app</option>
                  <option value="static_website">static_website</option>
                </select>
                <button class="btn" onclick="createProduct()">Create</button>
              </div>

              <div id="productsGrid" class="product-grid">Loading...</div>
              <pre id="productStatus"></pre>
            </div>
          </div>
        </section>
'''
    text = text.replace('<section id="view-skills" class="view">', section + '\n\n        <section id="view-skills" class="view">')

css = r'''
    /* TITAN_PRODUCT_LAUNCHER_START */
    .product-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
      margin-top: 14px;
    }

    .product-card {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.045);
      border-radius: 18px;
      padding: 14px;
      display: grid;
      gap: 10px;
      min-height: 170px;
    }

    .product-title {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
      font-weight: 850;
    }

    .product-meta {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
      white-space: pre-wrap;
    }

    .product-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: auto;
    }

    @media (max-width: 980px) {
      .product-grid {
        grid-template-columns: 1fr;
      }
    }
    /* TITAN_PRODUCT_LAUNCHER_END */
'''

if "TITAN_PRODUCT_LAUNCHER_START" not in text:
    text = text.replace("</style>", css + "\n  </style>", 1)

js = r'''
// TITAN_PRODUCT_LAUNCHER_JS_START
async function loadProducts() {
  const data = await jsonFetch("/api/product/list");
  const grid = document.getElementById("productsGrid");
  const status = document.getElementById("productStatus");

  if (!grid) return;

  const products = data.products || [];

  if (!products.length) {
    grid.textContent = "No products yet.";
    if (status) status.textContent = "";
    return;
  }

  grid.innerHTML = "";

  products.forEach(p => {
    const card = document.createElement("div");
    card.className = "product-card";

    const title = document.createElement("div");
    title.className = "product-title";

    const name = document.createElement("span");
    name.textContent = p.name;

    const pill = document.createElement("span");
    pill.className = "status-pill " + (p.running ? "done" : "");
    pill.textContent = p.running ? "running" : "stopped";

    title.appendChild(name);
    title.appendChild(pill);

    const meta = document.createElement("div");
    meta.className = "product-meta";
    meta.textContent = `kind: ${p.kind}\nurl: ${p.url || "-"}\npid: ${p.pid || "-"}\npath: ${p.path}`;

    const actions = document.createElement("div");
    actions.className = "product-actions";

    const start = document.createElement("button");
    start.className = "btn";
    start.textContent = "Start";
    start.onclick = () => startProduct(p.name);

    const stop = document.createElement("button");
    stop.className = "btn";
    stop.textContent = "Stop";
    stop.onclick = () => stopProduct(p.name);

    const logs = document.createElement("button");
    logs.className = "btn";
    logs.textContent = "Logs";
    logs.onclick = () => productLogs(p.name);

    actions.appendChild(start);
    actions.appendChild(stop);
    actions.appendChild(logs);

    if (p.url) {
      const open = document.createElement("button");
      open.className = "btn primary";
      open.textContent = "Open";
      open.onclick = () => window.open(p.url, "_blank");
      actions.appendChild(open);
    }

    card.appendChild(title);
    card.appendChild(meta);
    card.appendChild(actions);
    grid.appendChild(card);
  });
}

async function createProduct() {
  const name = document.getElementById("productName").value.trim();
  const kind = document.getElementById("productKind").value;
  const status = document.getElementById("productStatus");

  if (!name) {
    status.textContent = "Enter a product name.";
    return;
  }

  const data = await jsonFetch("/api/product/create", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({name, kind, description: "Created from Titan dashboard."})
  });

  status.textContent = JSON.stringify(data, null, 2);
  await loadProducts();
}

async function startProduct(name) {
  const status = document.getElementById("productStatus");
  const data = await jsonFetch("/api/product/start", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({name})
  });
  status.textContent = JSON.stringify(data, null, 2);
  await loadProducts();
}

async function stopProduct(name) {
  const status = document.getElementById("productStatus");
  const data = await jsonFetch("/api/product/stop", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({name})
  });
  status.textContent = JSON.stringify(data, null, 2);
  await loadProducts();
}

async function productLogs(name) {
  const status = document.getElementById("productStatus");
  const data = await jsonFetch("/api/product/logs?name=" + encodeURIComponent(name));
  status.textContent = JSON.stringify(data, null, 2);
}
// TITAN_PRODUCT_LAUNCHER_JS_END
'''

if "TITAN_PRODUCT_LAUNCHER_JS_START" not in text:
    text = text.replace("</script>", js + "\n</script>", 1)

routes = r'''
@app.route("/api/product/list")
def api_product_list():
    from agent_core.products import list_products
    return safe(lambda: {"products": list_products()})


@app.route("/api/product/create", methods=["POST"])
def api_product_create():
    from agent_core.products import create_product
    return safe(lambda: {"result": create_product(request.json.get("name", ""), request.json.get("kind", "python_cli"), request.json.get("description", ""))})


@app.route("/api/product/start", methods=["POST"])
def api_product_start():
    from agent_core.products import start_product
    return safe(lambda: start_product(request.json.get("name", "")))


@app.route("/api/product/stop", methods=["POST"])
def api_product_stop():
    from agent_core.products import stop_product
    return safe(lambda: stop_product(request.json.get("name", "")))


@app.route("/api/product/logs")
def api_product_logs():
    from agent_core.products import product_logs
    return safe(lambda: product_logs(request.args.get("name", "")))

'''

if '@app.route("/api/product/list")' not in text:
    text = text.replace('\n\nif __name__ == "__main__":', "\n\n" + routes + '\nif __name__ == "__main__":')

path.write_text(text, encoding="utf-8")
print("Patched dashboard product launcher.")
PY

python3 patch_dashboard_products.py

echo "[4/4] Verifying..."

python3 -m py_compile agent_core/products.py titan_terminal.py control_panel.py

cat > docs/PHASE12_PRODUCT_LAUNCHER.md <<EOF
# Phase 12 Product Launcher

Timestamp: $STAMP

Added:
- agent_core/products.py
- terminal product commands
- dashboard Products tab
- product create/start/stop/logs APIs

Terminal:
- /products
- /product-create <name> [python_cli|flask_app|static_website]
- /product-start <name>
- /product-stop <name>
- /product-logs <name>

Dashboard:
- Products tab
- Create product
- Start product
- Stop product
- Open URL
- View logs

Next:
- global workspace search
- file diff viewer
- product build templates
EOF

echo "Phase 12 complete."
