from pathlib import Path
import re

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

backup = Path("backups/titan_terminal_before_video_motion_command.py")
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

helper = r'''
def terminal_video_motion(args):
    try:
        import json
        from agent_core.video_tools import set_video_motion
        result = set_video_motion(args)
        say_panel(json.dumps(result, indent=2), title="Video Motion", style="green")
    except Exception as e:
        say_panel("Video motion failed: " + repr(e), title="Video Motion", style="red")


'''

if "def terminal_video_motion(" not in text:
    text = text.replace("def repl():", helper + "\ndef repl():", 1)

intercept = r'''
            if lower.startswith("/video-motion "):
                terminal_video_motion(command.replace("/video-motion ", "", 1).strip())
                continue

'''

if 'lower.startswith("/video-motion ")' not in text:
    repl_start = text.find("def repl():")
    after = text[repl_start:]
    match = re.search(r"\n\s*if\s+lower\b", after)
    if not match:
        raise SystemExit("Could not find command insertion point.")
    pos = repl_start + match.start()
    text = text[:pos] + intercept + text[pos:]

path.write_text(text, encoding="utf-8")
print("Installed /video-motion command.")
