from pathlib import Path
import re
import json

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
cfg_path = BASE / "config.json"
cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
cfg["image_backend"] = "comfyui"
cfg["image_width"] = 768
cfg["image_height"] = 768
cfg["comfy_steps"] = 4
cfg["comfy_cfg"] = 1.0
cfg_path.write_text(json.dumps(cfg, indent=2))

path = BASE / "agent_core" / "image_tools.py"
text = path.read_text(encoding="utf-8")

backup = BASE / "backups" / "image_tools_before_comfyui.py"
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

pattern = r"def create_image\(prompt,.*?\n(?=def create_gif\()"

replacement = '''def create_image(prompt, width=None, height=None, open_file=True):
    cfg = load_config()
    backend = cfg.get("image_backend", "pollinations")
    prompt = clean_prompt(prompt)

    width = int(width or cfg.get("image_width", 768))
    height = int(height or cfg.get("image_height", 768))

    if backend == "comfyui":
        from agent_core.comfyui_bridge import comfy_image
        return comfy_image(
            prompt,
            width=width,
            height=height,
            steps=int(cfg.get("comfy_steps", 4)),
            cfg=float(cfg.get("comfy_cfg", 1.0)),
        )

    path = OUT / f"{stamp()}_{slug(prompt)}.png"

    if backend == "pollinations":
        try:
            url = pollinations_url(prompt, width, height)
            download_image(url, path)
            used_backend = "pollinations-flux"
        except Exception as e:
            img = local_fallback_image(prompt, width, height)
            path = OUT / f"{stamp()}_{slug(prompt)}_fallback.png"
            img.save(path)
            used_backend = "local fallback after pollinations error: " + repr(e)
    else:
        img = local_fallback_image(prompt, width, height)
        img.save(path)
        used_backend = "local fallback"

    if open_file:
        try:
            subprocess.Popen(["open", str(path)])
        except Exception:
            pass

    return {
        "result": "image created",
        "backend": used_backend,
        "prompt": prompt,
        "path": str(path),
    }


'''

new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count == 0:
    raise SystemExit("Could not patch create_image in image_tools.py")

path.write_text(new_text, encoding="utf-8")
print("image_tools now routes image_backend=comfyui to local ComfyUI")
