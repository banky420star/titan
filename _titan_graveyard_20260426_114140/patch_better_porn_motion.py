from pathlib import Path
import re

# Improve video_tools.py for real character motion
vpath = Path("agent_core/video_tools.py")
text = vpath.read_text(encoding="utf-8")

# Add stronger motion simulation
improved = '''
def create_explicit_video(prompt, seconds=10, fps=24, motion="high"):
    """Explicit porn video with actual character movement"""
    cfg = load_config()
    prompt = clean_prompt(prompt)
    
    # Force explicit + motion keywords
    motion_boost = ", dynamic motion, thrusting, bouncing breasts, hip movement, fluids, realistic physics, detailed penetration" if "sex" in prompt.lower() or "fuck" in prompt.lower() else ""
    
    enhanced = f"highly realistic explicit scene: {prompt}{motion_boost}, smooth animation, natural movement, cinematic"
    
    # Use higher quality settings for porn
    return create_video(enhanced, 
                       seconds=seconds, 
                       fps=fps, 
                       motion_strength=0.85 if motion=="high" else 0.6)
'''

# Insert improved function
if "def create_video" in text:
    text = re.sub(r'def create_video\(.*?\):.*?(?=\n\n|\n\s*def )', improved, text, flags=re.DOTALL)

vpath.write_text(text, encoding="utf-8")
print("✅ Better explicit motion patch applied")
