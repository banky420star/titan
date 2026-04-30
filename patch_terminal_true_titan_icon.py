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

        def seg(chars, style):
            logo.append(chars, style=style)

        # Titan official-icon style:
        # left yellow rounded block, tall orange middle block, coral right block, two eyes.
        logo.append("\n")
        seg("          ", "")
        seg("      ", "on #FFC46B")
        logo.append("\n")

        seg("          ", "")
        seg("      ", "on #FFB25B")
        logo.append("\n")

        seg("          ", "")
        seg("      ", "on #FFA04B")
        logo.append("\n")

        seg("      ", "")
        seg("      ", "on #FFE66D")
        seg("      ", "on #FF963F")
        seg("      ", "on #FF6B6F")
        logo.append("\n")

        seg("      ", "")
        seg("      ", "on #FFD93D")
        seg("  ●   ", "bold #111827 on #FF8F38")
        seg("  ●   ", "bold #111827 on #FF5B63")
        logo.append("\n")

        seg("      ", "")
        seg("      ", "on #FFD02E")
        seg("      ", "on #FF8730")
        seg("      ", "on #FF535D")
        logo.append("\n")

        seg("      ", "")
        seg("      ", "on #FFC928")
        seg("      ", "on #FF7F28")
        seg("      ", "on #F84A57")
        logo.append("\n")

        seg("          ", "")
        seg("      ", "on #FF7924")
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
            "          ██████\n"
            "          ██████\n"
            "          ██████\n"
            "      ██████████████████\n"
            "      ██████ ●  ███ ●  █\n"
            "      ██████████████████\n"
            "      ██████████████████\n"
            "          ██████\n\n"
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

print("Patched terminal startup to match the real Titan icon shape.")
