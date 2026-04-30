from pathlib import Path
term = Path("titan_terminal.py")
text = term.read_text(encoding="utf-8")

handler = '''
            if lower.startswith("/porn "):
                prompt = command[6:].strip()
                try:
                    from agent_core.video_tools import create_explicit_video
                    result = create_explicit_video(prompt, seconds=10, fps=24)
                    print("✅ Explicit video command received:")
                    print(result)
                except Exception as e:
                    print("❌ Video error:", str(e))
                continue
'''

if "/porn " not in text:
    pos = text.find("def repl():")
    if pos > -1:
        insert_point = text.find("if lower.startswith", pos)
        if insert_point > -1:
            text = text[:insert_point] + handler + text[insert_point:]
        else:
            text = text[:pos+20] + handler + text[pos+20:]

term.write_text(text, encoding="utf-8")
print("✅ /porn command fixed in titan_terminal.py")
