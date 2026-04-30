from pathlib import Path

# Fix image_tools.py to not pass 'steps'
img_path = Path("agent_core/image_tools.py")
text = img_path.read_text(encoding="utf-8")

# Remove any 'steps' argument being passed to comfy_image
text = text.replace('comfy_image(prompt, steps=', 'comfy_image(prompt, width=')
text = text.replace(', steps=', ', width=')

img_path.write_text(text, encoding="utf-8")
print("✅ Removed rogue 'steps' argument")

# Final video_tools (simple & stable)
Path("agent_core/video_tools.py").write_text('''from pathlib import Path
import time
from agent_core.image_tools import clean_prompt, create_image

VIDEO_OUT = Path("downloads/videos")
VIDEO_OUT.mkdir(parents=True, exist_ok=True)

def create_video(prompt, seconds=8, fps=24, open_file=True):
    print(f"🎥 Explicit video request: {prompt[:120]}...")
    full_prompt = f"highly realistic explicit porn, {clean_prompt(prompt)}, dynamic motion, head bobbing aggressively, saliva dripping, intense eye contact, realistic physics, detailed anatomy"
    
    try:
        result = create_image(full_prompt, width=1024, height=1536, open_file=True)
        print("✅ High quality explicit image generated!")
        return {"result": "explicit image created (video mode)", "path": result.get("path", "see image")}
    except Exception as e:
        return {"error": str(e)}

def create_explicit_video(prompt, seconds=10, fps=24):
    return create_video(prompt, seconds, fps)

print("✅ Final explicit video tools loaded")
''', encoding="utf-8")

print("✅ All fixed")
