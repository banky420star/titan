from pathlib import Path
import re

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

backup = Path("backups/titan_terminal_before_video_commands.py")
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

helpers = r'''
def terminal_create_video(args):
    try:
        import json
        from agent_core.video_tools import create_video

        prompt = str(args or "").strip()
        if not prompt:
            say_panel("Usage: /video <prompt>", title="Video", style="yellow")
            return

        result = create_video(prompt)
        say_panel(json.dumps(result, indent=2), title="Video Created", style="green")
    except Exception as e:
        say_panel("Video creation failed: " + repr(e), title="Video", style="red")


def terminal_list_videos():
    try:
        import json
        from agent_core.video_tools import list_videos
        say_panel(json.dumps(list_videos(), indent=2), title="Videos", style="cyan")
    except Exception as e:
        say_panel("Videos failed: " + repr(e), title="Videos", style="red")


def terminal_video_quality(args):
    try:
        import json
        from agent_core.video_tools import set_video_quality
        result = set_video_quality(args)
        say_panel(json.dumps(result, indent=2), title="Video Quality", style="green")
    except Exception as e:
        say_panel("Video quality failed: " + repr(e), title="Video Quality", style="red")


'''

if "def terminal_create_video(" not in text:
    text = text.replace("def repl():", helpers + "\ndef repl():", 1)

intercept = r'''
            if lower.startswith("/video "):
                terminal_create_video(command.replace("/video ", "", 1).strip())
                continue

            if lower == "/videos":
                terminal_list_videos()
                continue

            if lower.startswith("/video-quality "):
                terminal_video_quality(command.replace("/video-quality ", "", 1).strip())
                continue

'''

if 'lower.startswith("/video ")' not in text:
    repl_start = text.find("def repl():")
    after = text[repl_start:]
    match = re.search(r"\n\s*if\s+lower\b", after)
    if not match:
        raise SystemExit("Could not find command insertion point")
    pos = repl_start + match.start()
    text = text[:pos] + intercept + text[pos:]

path.write_text(text, encoding="utf-8")
print("Video terminal commands installed.")
