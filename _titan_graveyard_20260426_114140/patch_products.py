from pathlib import Path

path = Path("agent_v3.py")
text = path.read_text()

marker = "def tool(name, inp):"
if marker not in text:
    raise SystemExit("Could not find tool() in agent_v3.py")

product_code = r'''
PRODUCTS_DIR = Path(CONFIG.get("products_dir", str(BASE / "products")))
PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)


def list_products():
    PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
    items = []
    for p in sorted(PRODUCTS_DIR.iterdir()):
        if p.is_dir():
            items.append(str(p))
    return "\n".join(items) if items else "No products found."


def create_product(name, kind="python_cli", description=""):
    name = safe_name(name)
    kind = str(kind or "python_cli").strip().lower()
    root = PRODUCTS_DIR / name
    root.mkdir(parents=True, exist_ok=True)

    if kind in ["flask", "flask_app", "flask-app", "webapp"]:
        (root / "templates").mkdir(exist_ok=True)
        (root / "static").mkdir(exist_ok=True)

        files = {
            "app.py": "from flask import Flask, render_template\n\napp = Flask(__name__)\n\n@app.route('/')\ndef home():\n    return render_template('index.html')\n\n@app.route('/health')\ndef health():\n    return {'status': 'ok'}\n\nif __name__ == '__main__':\n    app.run(debug=True, port=5055)\n",
            "requirements.txt": "flask\n",
            "templates/index.html": "<!doctype html>\n<html>\n<head>\n  <meta charset='utf-8'>\n  <title>Titan Product</title>\n  <link rel='stylesheet' href='/static/style.css'>\n</head>\n<body>\n  <main>\n    <h1>Titan Product</h1>\n    <p>Product scaffold online.</p>\n  </main>\n</body>\n</html>\n",
            "static/style.css": "body {\n  margin: 0;\n  font-family: system-ui, sans-serif;\n  background: #080a12;\n  color: #f8fafc;\n}\n\nmain {\n  max-width: 900px;\n  margin: 90px auto;\n  padding: 32px;\n  border-radius: 24px;\n  background: #111827;\n}\n",
            "README.md": "# " + name + "\n\n" + description + "\n\nRun:\n  pip install -r requirements.txt\n  python3 app.py\n"
        }
    else:
        files = {
            "main.py": "def main():\n    print('Titan product scaffold online.')\n\nif __name__ == '__main__':\n    main()\n",
            "requirements.txt": "",
            "README.md": "# " + name + "\n\n" + description + "\n\nRun:\n  python3 main.py\n"
        }

    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    return "Created product scaffold: " + str(root)
'''

if "def list_products(" not in text:
    text = text.replace(marker, product_code + "\n" + marker)

unknown = '    return f"Unknown tool: {name}"'
if unknown not in text:
    raise SystemExit("Could not find unknown-tool return")

entries = '''    if name == "create_product": return create_product(inp.get("name") or "", inp.get("kind") or "python_cli", inp.get("description") or "")
    if name == "list_products": return list_products()
'''

if 'if name == "list_products"' not in text:
    text = text.replace(unknown, entries + unknown)

path.write_text(text)
print("Added list_products() and create_product() to agent_v3.py")
