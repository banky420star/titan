from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text()

start = text.find("def startup():")
if start == -1:
    raise SystemExit("Could not find startup()")

end = text.find("\ndef help_menu():", start)
if end == -1:
    raise SystemExit("Could not find help_menu() after startup()")

new_startup = r'''def startup():
    cfg = load_config()

    if console and Panel and Text:
        logo = Text()

        def seg(chars, style=""):
            logo.append(chars, style=style)

        logo.append("\n")
        # top cap for taller middle bar
        seg("            ")
        seg("    ", "on #F59E0B")
        logo.append("\n")

        for row in range(6):
            seg("        ")
            if row == 2:
                seg("    ", "on #F6E05E")
                seg(" ●● ", "bold #0F172A on #F59E0B")
                seg("    ", "on #F87171")
            else:
                seg("    ", "on #F6E05E")
                seg("    ", "on #F59E0B")
                seg("    ", "on #F87171")
            logo.append("\n")

        # bottom cap for taller middle bar
        seg("            ")
        seg("    ", "on #F59E0B")
        logo.append("\n\n")

        body = Text()
        body.append(logo)
        body.append("Titan clean terminal\n", style="bold white")
        body.append(f"Base: {BASE}\n", style="dim")
        body.append(f"Workspace: {cfg.get('workspace', BASE / 'workspace')}\n", style="dim")
        body.append(f"Model: {cfg.get('model', 'unset')}\n", style="cyan")
        body.append(f"Fallback: {cfg.get('fallback_model', 'unset')}\n", style="cyan")
        body.append("Dashboard: http://127.0.0.1:5050\n", style="green")

        console.print(Panel(body, title="Titan", border_style="magenta"))

    else:
        body = (
            "\n"
            "            ████\n"
            "        ████ ████ ████\n"
            "        ████ ████ ████\n"
            "        ████ ●● ████\n"
            "        ████ ████ ████\n"
            "        ████ ████ ████\n"
            "        ████ ████ ████\n"
            "            ████\n\n"
            "Titan clean terminal\n"
            f"Base: {BASE}\n"
            f"Workspace: {cfg.get('workspace', BASE / 'workspace')}\n"
            f"Model: {cfg.get('model', 'unset')}\n"
            f"Fallback: {cfg.get('fallback_model', 'unset')}\n"
            "Dashboard: http://127.0.0.1:5050\n"
        )
        say_panel(body, title="Titan", style="magenta")
'''

text = text[:start] + new_startup + text[end:]
path.write_text(text)
print("Patched terminal startup to 3-bar icon with taller middle bar.")
