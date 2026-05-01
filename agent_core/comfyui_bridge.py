"""ComfyUI bridge — connects to a local ComfyUI instance for image generation."""

import subprocess
import sys
from pathlib import Path

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
COMFYUI_DIR = BASE / "local_ai" / "ComfyUI"
# Fallback: check old path if new one doesn't exist
if not COMFYUI_DIR.exists():
    _alt = BASE / "models" / "ComfyUI"
    if _alt.exists():
        COMFYUI_DIR = _alt
COMFYUI_URL = "http://127.0.0.1:8188"
_comfy_process = None


def _load_config():
    import json
    cfg_path = BASE / "config.json"
    if cfg_path.exists():
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    return {}


def comfy_info():
    """Return ComfyUI connection status and config."""
    import json
    import urllib.request

    cfg = _load_config()
    status = {
        "running": False,
        "url": COMFYUI_URL,
        "image_backend": cfg.get("image_backend", "pollinations"),
        "comfy_steps": cfg.get("comfy_steps", 4),
        "comfy_cfg": cfg.get("comfy_cfg", 1.0),
    }

    try:
        req = urllib.request.Request(COMFYUI_URL, headers={"User-Agent": "TitanAgent/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                status["running"] = True
    except Exception:
        pass

    return status


def comfy_status():
    """Alias for comfy_info."""
    return comfy_info()


def start_comfyui():
    """Start ComfyUI server if not already running."""
    global _comfy_process

    info = comfy_info()
    if info["running"]:
        return {"result": "already running", "url": COMFYUI_URL}

    main_py = COMFYUI_DIR / "main.py"
    if not main_py.exists():
        return {"error": f"ComfyUI not found at {COMFYUI_DIR}"}

    try:
        _comfy_process = subprocess.Popen(
            [sys.executable, str(main_py), "--listen", "127.0.0.1", "--port", "8188"],
            cwd=str(COMFYUI_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return {"result": "ComfyUI starting", "url": COMFYUI_URL, "pid": _comfy_process.pid}
    except Exception as e:
        return {"error": f"Failed to start ComfyUI: {e}"}


def stop_comfyui():
    """Stop the ComfyUI server process."""
    global _comfy_process

    if _comfy_process is not None and _comfy_process.poll() is None:
        _comfy_process.terminate()
        try:
            _comfy_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _comfy_process.kill()
        _comfy_process = None
        return {"result": "ComfyUI stopped"}

    try:
        result = subprocess.run(
            ["pkill", "-f", "ComfyUI"],
            capture_output=True, timeout=5,
        )
        if result.returncode == 0:
            return {"result": "ComfyUI process killed"}
    except Exception:
        pass

    return {"result": "No ComfyUI process found"}


def _find_checkpoint():
    """Find an available checkpoint in ComfyUI's models directory."""
    ckpt_dir = COMFYUI_DIR / "models" / "checkpoints"
    if not ckpt_dir.exists():
        return None
    for ext in ["*.safetensors", "*.ckpt", "*.pt"]:
        for f in sorted(ckpt_dir.rglob(ext)):
            return f.name
    return None


def comfy_image(prompt, width=1024, height=1536):
    """Generate an image by sending a workflow to ComfyUI.

    This talks DIRECTLY to ComfyUI's API — does NOT call media_engine.create_image.
    Raises RuntimeError if ComfyUI is not running or generation fails.
    """
    import json
    import urllib.request
    import ssl

    info = comfy_info()
    if not info["running"]:
        raise RuntimeError("ComfyUI is not running")

    checkpoint = _find_checkpoint()
    if not checkpoint:
        raise RuntimeError("No checkpoint found in ComfyUI models directory")

    cfg = _load_config()
    steps = int(cfg.get("comfy_steps", 4))
    cfg_scale = float(cfg.get("comfy_cfg", 1.0))

    # Minimal SD/SDXL text-to-image workflow
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": abs(hash(prompt)) % 999999999,
                "steps": steps,
                "cfg": cfg_scale,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            }
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": checkpoint}
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1}
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["4", 1]}
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "low quality, blurry, distorted, watermark, text, extra limbs",
                "clip": ["4", 1]
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "titan", "images": ["8", 0]}
        }
    }

    payload = {"prompt": workflow}

    ctx = ssl._create_unverified_context() if not cfg.get("verify_ssl", True) else ssl.create_default_context()
    req = urllib.request.Request(
        COMFYUI_URL + "/prompt",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=180, context=ctx) as resp:
        data = json.loads(resp.read())

    prompt_id = data.get("prompt_id")

    # Poll for completion
    import time
    for _ in range(60):
        time.sleep(3)
        try:
            hist_req = urllib.request.Request(
                f"{COMFYUI_URL}/history/{prompt_id}",
                headers={"User-Agent": "TitanAgent/1.0"},
            )
            with urllib.request.urlopen(hist_req, timeout=10, context=ctx) as hist_resp:
                hist = json.loads(hist_resp.read())
                if prompt_id in hist:
                    outputs = hist[prompt_id].get("outputs", {})
                    images = outputs.get("9", {}).get("images", [])
                    if images:
                        img_data = images[0]
                        filename = img_data["filename"]
                        subfolder = img_data.get("subfolder", "")
                        img_url = f"{COMFYUI_URL}/view?filename={filename}"
                        if subfolder:
                            img_url += f"&subfolder={subfolder}"
                        from agent_core.media_engine import IMAGE_OUT, stamp, slug
                        out_path = IMAGE_OUT / f"{stamp()}_{slug(prompt)}.png"
                        img_req = urllib.request.Request(img_url, headers={"User-Agent": "TitanAgent/1.0"})
                        with urllib.request.urlopen(img_req, timeout=30, context=ctx) as img_resp:
                            out_path.write_bytes(img_resp.read())
                        return {
                            "result": "image created",
                            "backend": "comfyui",
                            "prompt": prompt,
                            "path": str(out_path),
                        }
        except Exception:
            continue

    raise RuntimeError("ComfyUI generation timed out")


def queue_prompt(workflow=None, positive=None):
    """Queue a prompt on ComfyUI."""
    prompt = positive or "image generation prompt"
    return comfy_image(prompt)