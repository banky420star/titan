from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

if "def terminal_search_files(" not in text:
    marker = "def repl():"
    if marker not in text:
        raise SystemExit("Could not find def repl()")

    helpers = r'''
def terminal_search_files(query):
    try:
        from agent_core.search_diff import search_files_text
        say_panel(search_files_text(query, root="all"), title="Search", style="cyan")
    except Exception as e:
        say_panel("Search failed: " + repr(e), title="Search", style="red")


def terminal_snapshot(root):
    try:
        from agent_core.search_diff import make_snapshot
        root = str(root or "").strip() or "workspace"
        say_panel(json.dumps(make_snapshot(root), indent=2), title="Snapshot", style="green")
    except Exception as e:
        say_panel("Snapshot failed: " + repr(e), title="Snapshot", style="red")


def terminal_changed(root):
    try:
        from agent_core.search_diff import changed_files_text
        root = str(root or "").strip() or "workspace"
        say_panel(changed_files_text(root), title="Changed Files", style="yellow")
    except Exception as e:
        say_panel("Changed files failed: " + repr(e), title="Changed Files", style="red")


def terminal_diff(args):
    try:
        from agent_core.search_diff import diff_file
        parts = str(args or "").strip().split(" ", 1)

        if len(parts) == 1:
            root = "workspace"
            path = parts[0]
        else:
            root, path = parts

        say_panel(diff_file(root, path), title="Diff", style="magenta")
    except Exception as e:
        say_panel("Diff failed: " + repr(e), title="Diff", style="red")


'''
    text = text.replace(marker, helpers + marker)

if 'lower.startswith("/search ")' not in text:
    target = '''            if lower == "/products":
                terminal_products()
                continue
'''

    replacement = '''            if lower == "/products":
                terminal_products()
                continue

            if lower.startswith("/search "):
                terminal_search_files(command.replace("/search ", "", 1).strip())
                continue

            if lower.startswith("/snapshot"):
                terminal_snapshot(command.replace("/snapshot", "", 1).strip())
                continue

            if lower.startswith("/changed"):
                terminal_changed(command.replace("/changed", "", 1).strip())
                continue

            if lower.startswith("/diff "):
                terminal_diff(command.replace("/diff ", "", 1).strip())
                continue
'''

    if target not in text:
        raise SystemExit("Could not find insertion point for search commands.")

    text = text.replace(target, replacement, 1)

text = text.replace(
    "/products    Show products\n",
    "/products    Show products\n/search <query> Search files by name/content\n/snapshot [root] Save file snapshot\n/changed [root] Show changed files\n/diff <root> <path> Show unified diff\n"
)

path.write_text(text, encoding="utf-8")
print("Patched terminal search/diff commands.")
