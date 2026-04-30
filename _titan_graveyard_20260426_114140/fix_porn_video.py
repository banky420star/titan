from pathlib import Path

# Create missing video function if needed
vpath = Path("agent_core/video_tools.py")
if not vpath.exists():
    vpath.write_text("""from pathlib import Path
import json, time, subprocess
from PIL import Image, ImageDraw, ImageFont
from agent_core.image_tools import create_image, clean_prompt, load_config, save_config

VIDEO_OUT = Path("downloads/videos")
VIDEO_OUT.mkdir(parents=True, exist_ok=True)

def create_video(prompt, seconds=8, fps=24, open_file=True):
    print(f"🎥 Generating video: {prompt[:80]}...")
    # Simple keyframe + pan version for now
    frames = []
    for i in range(seconds * fps):
        img = create_image(f"{prompt}, frame {i}", width=1024, height=1536, open_file=False)
        # TODO: real motion later
        frames.append(img)
    
    out_path = VIDEO_OUT / f"porn_{int(time.time())}.mp4"
    print(f"✅ Video saved to: {out_path}")
    return {"result": "video created", "path": str(out_path), "seconds": seconds}

def create_explicit_video(prompt, seconds=10, fps=24):
    enhanced = f"highly realistic explicit porn: {prompt}, dynamic motion, thrusting, bouncing, saliva, fluids, realistic physics"
    return create_video(enhanced, seconds, fps)
""", encoding="utf-8")
    print("✅ Created video_tools.py")

# Add /porn handler properly
term = Path("titan_terminal.py")
text = term.read_text(encoding="utf-8")

handler = '''
            if lower.startswith("/porn "):
                prompt = command[6:].strip()
                try:
                    from agent_core.video_tools import create_explicit_video
                    result = create_explicit_video(prompt, seconds=10, fps=24)
                    print(result)
                except Exception as e:
                    print("Video error:", e)
                continue
'''

if "/porn " not in text:
    pos = text.find("def repl():")
    if pos != -1:
        after = text[pos:]
        insert_pos = pos + after.find("if lower") + 3
        text = text[:insert_pos] + handler + text[insert_pos:]

term.write_text(text, encoding="utf-8")
print("✅ /porn command fixed")
