from pathlib import Path
import re

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

backup = Path("backups/titan_terminal_before_comfyui_commands.py")
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

helpers = r'''
def terminal_comfy_status():
    try:
        import json
        from agent_core.comfyui_bridge import comfy_info
        say_panel(json.dumps(comfy_info(), indent=2), title="ComfyUI", style="cyan")
    except Exception as e:
        say_panel("ComfyUI status failed: " + repr(e), title="ComfyUI", style="red")


def terminal_comfy_start():
    try:
        import json
        from agent_core.comfyui_bridge import start_comfyui
        say_panel(json.dumps(start_comfyui(), indent=2), title="ComfyUI Start", style="green")
    except Exception as e:
        say_panel("ComfyUI start failed: " + repr(e), title="ComfyUI", style="red")


def terminal_comfy_stop():
    try:
        import json
        from agent_core.comfyui_bridge import stop_comfyui
        say_panel(json.dumps(stop_comfyui(), indent=2), title="ComfyUI Stop", style="yellow")
    except Exception as e:
        say_panel("ComfyUI stop failed: " + repr(e), title="ComfyUI", style="red")


def terminal_comfy_image(args):
    try:
        import json
        from agent_core.comfyui_bridge import comfy_image

        prompt = str(args or "").strip()
        if not prompt:
            say_panel("Usage: /comfy-image <prompt>", title="ComfyUI Image", style="yellow")
            return

        result = comfy_image(prompt)
        say_panel(json.dumps(result, indent=2), title="ComfyUI Image", style="green")
    except Exception as e:
        say_panel("ComfyUI image failed: " + repr(e), title="ComfyUI Image", style="red")


'''

if "def terminal_comfy_status(" not in text:
    text = text.replace("def repl():", helpers + "\ndef repl():", 1)

intercept = r'''
            if lower == "/comfy-status":
                terminal_comfy_status()
                continue

            if lower == "/comfy-start":
                terminal_comfy_start()
                continue

            if lower == "/comfy-stop":
                terminal_comfy_stop()
                continue

            if lower.startswith("/comfy-image "):
                terminal_comfy_image(command.replace("/comfy-image ", "", 1).strip())
                continue

'''

if 'lower == "/comfy-status"' not in text:
    repl_start = text.find("def repl():")
    after = text[repl_start:]
    match = re.search(r"\n\s*if\s+lower\b", after)
    if not match:
        raise SystemExit("Could not find command insertion point")
    pos = repl_start + match.start()
    text = text[:pos] + intercept + text[pos:]

path.write_text(text, encoding="utf-8")
print("ComfyUI terminal commands installed.")
