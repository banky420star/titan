from pathlib import Path
import re

path = Path("titan_terminal.py")
text = path.read_text()

start = text.find("def startup():")
if start == -1:
    raise SystemExit("Could not find startup()")

end = text.find("\ndef help_menu():", start)
if end == -1:
    raise SystemExit("Could not find help_menu() after startup()")

new_block = r'''def titan_logo_text(open_eyes=True):
    logo = Text()

    def seg(chars, style=""):
        logo.append(chars, style=style)

    eye_left = "  ●   " if open_eyes else "  ━   "
    eye_right = "  ●   " if open_eyes else "  ━   "

    logo.append("\n")

    # Taller middle bar top
    seg("                ")
    seg("        ", "on #F6A623")
    logo.append("\n")
    seg("                ")
    seg("        ", "on #F6A623")
    logo.append("\n")

    # Main three bars
    for row in range(2):
        seg("        ")
        seg("        ", "on #F8E45C")
        seg("        ", "on #F6A623")
        seg("        ", "on #EF7C73")
        logo.append("\n")

    # Cute eyes row
    seg("        ")
    seg("        ", "on #F8E45C")
    seg(eye_left, "bold #111827 on #F6A623")
    seg(eye_right, "bold #111827 on #EF7C73")
    logo.append("\n")

    # Soft lower body
    for row in range(3):
        seg("        ")
        seg("        ", "on #F8E45C")
        seg("        ", "on #F6A623")
        seg("        ", "on #EF7C73")
        logo.append("\n")

    # Middle bar bottom
    seg("                ")
    seg("        ", "on #F6A623")
    logo.append("\n")
    seg("                ")
    seg("        ", "on #F6A623")
    logo.append("\n")

    logo.append("\n")
    return logo


def startup_frame(open_eyes=True):
    cfg = load_config()

    body = Text()
    body.append(titan_logo_text(open_eyes=open_eyes))
    body.append("Titan clean terminal\n", style="bold white")
    body.append(f"Base: {BASE}\n", style="dim")
    body.append(f"Workspace: {cfg.get('workspace', BASE / 'workspace')}\n", style="dim")
    body.append(f"Model: {cfg.get('model', 'unset')}\n", style="cyan")
    body.append(f"Fallback: {cfg.get('fallback_model', 'unset')}\n", style="cyan")
    body.append("Dashboard: http://127.0.0.1:5050\n", style="green")

    console.print(Panel(body, title="Titan", border_style="magenta"))


def titan_prompt():
    # Tiny prompt icon: yellow bar, orange eye bar, coral eye bar.
    yellow = "\033[48;2;248;228;92m  \033[0m"
    orange_eye = "\033[48;2;246;166;35m● \033[0m"
    coral_eye = "\033[48;2;239;124;115m● \033[0m"
    return f"\n{yellow}{orange_eye}{coral_eye} titan ▸ "


def startup():
    cfg = load_config()

    if console and Panel and Text:
        # Blink animation: open → closed → open.
        try:
            for open_eyes, delay in [(True, 0.35), (False, 0.14), (True, 0.28)]:
                console.clear()
                startup_frame(open_eyes=open_eyes)
                time.sleep(delay)
        except Exception:
            startup_frame(open_eyes=True)

    else:
        body = (
            "\n"
            "                ████████\n"
            "                ████████\n"
            "        ████████ ████████ ████████\n"
            "        ████████ ████████ ████████\n"
            "        ████████   ●      ●  █████\n"
            "        ████████ ████████ ████████\n"
            "        ████████ ████████ ████████\n"
            "        ████████ ████████ ████████\n"
            "                ████████\n"
            "                ████████\n\n"
            "Titan clean terminal\n"
            f"Base: {BASE}\n"
            f"Workspace: {cfg.get('workspace', BASE / 'workspace')}\n"
            f"Model: {cfg.get('model', 'unset')}\n"
            f"Fallback: {cfg.get('fallback_model', 'unset')}\n"
            "Dashboard: http://127.0.0.1:5050\n"
        )
        say_panel(body, title="Titan", style="magenta")
'''

text = text[:start] + new_block + text[end:]

# Replace the prompt input line.
text = text.replace('command = input("\\ntitan > ").strip()', 'command = input(titan_prompt()).strip()')
text = text.replace('command = input("\\ntitan ▸ ").strip()', 'command = input(titan_prompt()).strip()')
text = text.replace('command = input("titan > ").strip()', 'command = input(titan_prompt()).strip()')
text = text.replace('command = input("titan ▸ ").strip()', 'command = input(titan_prompt()).strip()')

# Fallback regex if prompt was slightly different.
text = re.sub(
    r'command\s*=\s*input\([^)]*titan[^)]*\)\.strip\(\)',
    'command = input(titan_prompt()).strip()',
    text
)

path.write_text(text)
print("Patched Titan header, prompt icon, and startup blink.")
