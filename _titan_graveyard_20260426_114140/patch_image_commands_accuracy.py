from pathlib import Path
import re

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

backup = Path("backups/titan_terminal_before_image_accuracy_patch.py")
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

helpers = r'''
def terminal_create_image(args):
    try:
        import json
        from agent_core.image_tools import create_image

        prompt = str(args or "").strip()
        if not prompt:
            say_panel("Usage: /image <prompt>", title="Image", style="yellow")
            return

        result = create_image(prompt)
        say_panel(json.dumps(result, indent=2), title="Image Created", style="green")
    except Exception as e:
        say_panel("Image creation failed: " + repr(e), title="Image", style="red")


def terminal_create_gif(args):
    try:
        import json
        from agent_core.image_tools import create_gif

        prompt = str(args or "").strip()
        if not prompt:
            say_panel("Usage: /gif <prompt>", title="GIF", style="yellow")
            return

        result = create_gif(prompt)
        say_panel(json.dumps(result, indent=2), title="GIF Created", style="green")
    except Exception as e:
        say_panel("GIF creation failed: " + repr(e), title="GIF", style="red")


def terminal_list_images():
    try:
        import json
        from agent_core.image_tools import list_images
        say_panel(json.dumps(list_images(), indent=2), title="Images", style="cyan")
    except Exception as e:
        say_panel("Images failed: " + repr(e), title="Images", style="red")


def terminal_image_backend(args):
    try:
        import json
        from agent_core.image_tools import set_image_backend
        result = set_image_backend(args)
        say_panel(json.dumps(result, indent=2), title="Image Backend", style="green")
    except Exception as e:
        say_panel("Image backend failed: " + repr(e), title="Image Backend", style="red")


def terminal_image_enhance(args):
    try:
        import json
        from agent_core.image_tools import set_image_enhance
        result = set_image_enhance(args)
        say_panel(json.dumps(result, indent=2), title="Image Enhance", style="green")
    except Exception as e:
        say_panel("Image enhance failed: " + repr(e), title="Image Enhance", style="red")


'''

if "def terminal_create_image(" not in text:
    text = text.replace("def repl():", helpers + "\ndef repl():", 1)

intercept = r'''
            if lower.startswith("/image "):
                terminal_create_image(command.replace("/image ", "", 1).strip())
                continue

            if lower.startswith("/gif "):
                terminal_create_gif(command.replace("/gif ", "", 1).strip())
                continue

            if lower == "/images":
                terminal_list_images()
                continue

            if lower.startswith("/image-backend "):
                terminal_image_backend(command.replace("/image-backend ", "", 1).strip())
                continue

            if lower.startswith("/image-enhance "):
                terminal_image_enhance(command.replace("/image-enhance ", "", 1).strip())
                continue

'''

if 'lower.startswith("/image ")' not in text:
    repl_start = text.find("def repl():")
    after = text[repl_start:]
    match = re.search(r"\n\s*if\s+lower\b", after)
    if not match:
        raise SystemExit("Could not find command insertion point")
    pos = repl_start + match.start()
    text = text[:pos] + intercept + text[pos:]

path.write_text(text, encoding="utf-8")
print("image commands patched")
