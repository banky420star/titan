from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

backup = Path("backups/titan_terminal_before_product_helper_fix.py")
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

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
            say_panel("Usage: /product-create <name> [template]", title="Products", style="yellow")
            return

        name = parts[0]
        kind = parts[1] if len(parts) > 1 else "python_cli"

        result = create_product(name, kind, "Created from Titan terminal.")
        say_panel(str(result), title="Product Created", style="green")
    except Exception as e:
        say_panel("Create product failed: " + repr(e), title="Products", style="red")


def terminal_product_start(name):
    try:
        import json
        from agent_core.products import start_product
        result = start_product(name)
        say_panel(json.dumps(result, indent=2), title="Product Start", style="green")
    except Exception as e:
        say_panel("Start product failed: " + repr(e), title="Products", style="red")


def terminal_product_stop(name):
    try:
        import json
        from agent_core.products import stop_product
        result = stop_product(name)
        say_panel(json.dumps(result, indent=2), title="Product Stop", style="yellow")
    except Exception as e:
        say_panel("Stop product failed: " + repr(e), title="Products", style="red")


def terminal_product_logs(name):
    try:
        import json
        from agent_core.products import product_logs
        result = product_logs(name)
        say_panel(json.dumps(result, indent=2), title="Product Logs", style="magenta")
    except Exception as e:
        say_panel("Product logs failed: " + repr(e), title="Products", style="red")


'''

insert_before = "def repl():"
if insert_before not in text:
    raise SystemExit("Could not find def repl()")

needed = [
    "def terminal_products(",
    "def terminal_product_create(",
    "def terminal_product_start(",
    "def terminal_product_stop(",
    "def terminal_product_logs(",
]

missing = [x for x in needed if x not in text]

if missing:
    text = text.replace(insert_before, helpers + "\n" + insert_before, 1)

path.write_text(text, encoding="utf-8")
print("Patched missing product helpers:", ", ".join(missing) if missing else "none")
