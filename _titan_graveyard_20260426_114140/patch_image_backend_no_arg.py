from pathlib import Path
import re

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

backup = Path("backups/titan_terminal_before_image_backend_no_arg.py")
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

helper = r'''
def terminal_image_status():
    try:
        import json
        from pathlib import Path

        cfg_path = Path("config.json")
        cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}

        info = {
            "image_backend": cfg.get("image_backend", "local"),
            "image_enhance_prompt": cfg.get("image_enhance_prompt", False),
            "verify_ssl": cfg.get("verify_ssl", True),
            "usage": {
                "/image-backend local": "Use local fallback generator",
                "/image-backend pollinations": "Use web image generator",
                "/image-enhance on": "Enhance image prompts",
                "/image-enhance off": "Use exact prompt",
                "/image <prompt>": "Create image",
                "/gif <prompt>": "Create short GIF"
            }
        }

        say_panel(json.dumps(info, indent=2), title="Image Backend", style="cyan")
    except Exception as e:
        say_panel("Image backend status failed: " + repr(e), title="Image Backend", style="red")


'''

if "def terminal_image_status(" not in text:
    if "def repl():" not in text:
        raise SystemExit("Could not find def repl()")
    text = text.replace("def repl():", helper + "\ndef repl():", 1)

intercept = r'''
            if lower == "/image-backend":
                terminal_image_status()
                continue

            if lower == "/image-enhance":
                terminal_image_status()
                continue

'''

if 'lower == "/image-backend"' not in text:
    repl_start = text.find("def repl():")
    after = text[repl_start:]
    match = re.search(r"\n\s*if\s+lower\.startswith\(\"/image-backend \"\)", after)

    if match:
        pos = repl_start + match.start()
        text = text[:pos] + intercept + text[pos:]
    else:
        match = re.search(r"\n\s*if\s+lower\b", after)
        if not match:
            raise SystemExit("Could not find command insertion point")
        pos = repl_start + match.start()
        text = text[:pos] + intercept + text[pos:]

path.write_text(text, encoding="utf-8")
print("Patched /image-backend and /image-enhance no-arg status commands.")
