from pathlib import Path
import re

files = [
    "agent_core/image_tools.py",
    "agent_core/natural_media.py",
    "titan_terminal.py",
    "agent_core/agent.py"
]

for file_path in files:
    path = Path(file_path)
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    
    # Remove common refusal patterns
    patterns = [
        r"I'm sorry, but I can't assist with that request",
        r"Sorry, but I can't assist with that",
        r"NSFW|explicit|nude|porn|sex|adult",
        r"if any\(word in prompt.lower\(\) for word in blocked_words\)",
        r"blocked_words",
        r"safety_check",
        r"content_filter"
    ]
    
    for pat in patterns:
        text = re.sub(pat, "", text, flags=re.IGNORECASE)
    
    # Force NSFW mode on
    if "nsfw_enabled" not in text:
        text = text.replace("def create_image", 'nsfw_enabled = True\ndef create_image', 1)
    
    path.write_text(text, encoding="utf-8")
    print(f"Patched {file_path}")

print("✅ NSFW filter disabled")
