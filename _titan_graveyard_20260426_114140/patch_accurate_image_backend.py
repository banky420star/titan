from pathlib import Path
import json

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
CONFIG = BASE / "config.json"

cfg = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
cfg["image_backend"] = "pollinations"
cfg["verify_ssl"] = False
cfg["image_enhance_prompt"] = True
CONFIG.write_text(json.dumps(cfg, indent=2))

print("config patched: image_backend=pollinations, verify_ssl=false")
