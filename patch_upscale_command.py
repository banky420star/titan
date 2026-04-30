from pathlib import Path
import re

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

if "def terminal_upscale_image(" not in text:
    helper = r'''
def terminal_upscale_image(args):
    try:
        import json
        from agent_core.upscale_tools import upscale_image

        raw = str(args or "").strip()
        if not raw:
            say_panel("Usage: /upscale <file_path> [scale]", title="Upscale", style="yellow")
            return

        parts = raw.split()
        file_path = parts[0]
        scale = int(parts[1]) if len(parts) > 1 else 2

        result = upscale_image(file_path, scale=scale)
        say_panel(json.dumps(result, indent=2), title="Upscale", style="green")
    except Exception as e:
        say_panel("Upscale failed: " + repr(e), title="Upscale", style="red")

'''
    text = text.replace("def repl():", helper + "\ndef repl():", 1)

if 'lower.startswith("/upscale ")' not in text:
    repl_start = text.find("def repl():")
    after = text[repl_start:]
    match = re.search(r"\n\s*if\s+lower\b", after)
    if not match:
        raise SystemExit("Could not find insertion point")
    pos = repl_start + match.start()

    intercept = r'''
            if lower.startswith("/upscale "):
                terminal_upscale_image(command.replace("/upscale ", "", 1).strip())
                continue

'''
    text = text[:pos] + intercept + text[pos:]

path.write_text(text, encoding="utf-8")
print("Installed /upscale command.")
