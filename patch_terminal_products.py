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
