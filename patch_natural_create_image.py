from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

backup = Path("backups/titan_terminal_before_natural_create_image.py")
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

needle = "def run_titan_prompt(command):"
if needle not in text:
    raise SystemExit("Could not find run_titan_prompt(command)")

patch = '''def run_titan_prompt(command):
    # TITAN_NATURAL_MEDIA_ROUTER_V1
    try:
        from agent_core.natural_media import route_natural_media
        _media = route_natural_media(command)
        if _media and _media.get("handled"):
            return _media.get("text", "")
    except Exception as _media_error:
        return "Media request failed: " + repr(_media_error)

'''

if "TITAN_NATURAL_MEDIA_ROUTER_V1" not in text:
    text = text.replace(needle, patch, 1)

path.write_text(text, encoding="utf-8")
print("Natural create image / gif routing installed.")
