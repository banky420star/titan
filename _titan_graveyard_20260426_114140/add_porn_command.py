from pathlib import Path
import re

# Patch terminal
term = Path("titan_terminal.py")
text = term.read_text(encoding="utf-8")

porn_handler = '''
            if lower.startswith("/porn "):
                prompt = command.replace("/porn ", "", 1).strip()
                from agent_core.natural_media import route_natural_media
                result = route_natural_media(f"create explicit video of {prompt}")
                if result and result.get("handled"):
                    print(result.get("text"))
                else:
                    print("Creating explicit video...")
                    from agent_core.video_tools import create_video
                    res = create_video(f"highly realistic explicit porn scene: {prompt}", seconds=8, fps=24)
                    print(res)
                continue
'''

if "/porn " not in text:
    repl_start = text.find("def repl():")
    after = text[repl_start:]
    match = re.search(r"\n\s*if\s+lower\b", after)
    pos = repl_start + match.start()
    text = text[:pos] + porn_handler + text[pos:]

term.write_text(text, encoding="utf-8")
print("✅ /porn command added")
