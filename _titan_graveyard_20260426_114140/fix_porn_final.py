from pathlib import Path

# Fix image_tools.py - remove any 'steps' calls
img = Path("agent_core/image_tools.py")
text = img.read_text(encoding="utf-8")
text = text.replace("steps=", "width=").replace(", steps=", ", width=")
img.write_text(text, encoding="utf-8")
print("✅ Fixed steps argument in image_tools.py")

# Final simple video_tools
Path("agent_core/video_tools.py").write_text('''from pathlib import Path
import time
from agent_core.image_tools import create_image, clean_prompt

VIDEO_OUT = Path("downloads/videos")
VIDEO_OUT.mkdir(parents=True, exist_ok=True)

def create_video(prompt, seconds=8, fps=24, open_file=True):
    print(f"🎥 Explicit video request: {prompt[:100]}...")
    full_prompt = f"highly realistic explicit porn, {clean_prompt(prompt)}, dynamic motion, head bobbing, thrusting, bouncing breasts, saliva strings, eye contact, realistic physics, detailed anatomy"
    
    try:
        result = create_image(full_prompt, width=1024, height=1536, open_file=True)
        print("✅ High-quality explicit image generated!")
        return {"result": "explicit image created", "path": result.get("path")}
    except Exception as e:
        return {"error": str(e)}

def create_explicit_video(prompt, seconds=10, fps=24):
    return create_video(prompt, seconds, fps)

print("✅ Final explicit video tools loaded")
''', encoding="utf-8")
print("✅ video_tools.py reset to stable version")
