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
