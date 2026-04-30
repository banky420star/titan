from pathlib import Path
from datetime import datetime
import json
import random
import subprocess
import time
import urllib.parse
import urllib.request

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
COMFY = BASE / "local_ai" / "ComfyUI"
OUT = BASE / "downloads" / "images"
LOGS = BASE / "logs" / "comfyui"
PID_FILE = LOGS / "comfyui.pid"

HOST = "127.0.0.1"
PORT = 8188
URL = f"http://{HOST}:{PORT}"

OUT.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)


def now():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def api_get(path, timeout=5):
    with urllib.request.urlopen(URL + path, timeout=timeout) as r:
        return r.read()


def api_json(path, timeout=5):
    return json.loads(api_get(path, timeout).decode("utf-8"))


def api_post(path, payload, timeout=30):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def comfy_status():
    installed = COMFY.exists()
    checkpoints = []

    ckpt_dir = COMFY / "models" / "checkpoints"
    if ckpt_dir.exists():
        checkpoints = [p.name for p in sorted(ckpt_dir.glob("*.safetensors"))]

    try:
        api_get("/system_stats", timeout=2)
        running = True
        error = None
    except Exception as e:
        running = False
        error = repr(e)

    return {
        "installed": installed,
        "running": running,
        "url": URL,
        "checkpoints": checkpoints,
        "error": error,
        "install_note": "Expected ComfyUI folder: /Volumes/AI_DRIVE/TitanAgent/local_ai/ComfyUI"
    }


def start_comfyui():
    status = comfy_status()

    if status.get("running"):
        return {"result": "already running", "url": URL, "status": status}

    if not COMFY.exists():
        return {
            "error": "ComfyUI is not installed.",
            "expected_path": str(COMFY),
            "next": "Install ComfyUI first, then run /comfy-start again."
        }

    script = BASE / "scripts" / "start_comfyui.sh"
    stdout = LOGS / "comfyui.stdout.log"
    stderr = LOGS / "comfyui.stderr.log"

    p = subprocess.Popen(
        [str(script)],
        cwd=str(BASE),
        stdout=stdout.open("a"),
        stderr=stderr.open("a"),
        start_new_session=True,
    )

    PID_FILE.write_text(str(p.pid), encoding="utf-8")

    for _ in range(90):
        status = comfy_status()
        if status.get("running"):
            return {
                "result": "started",
                "pid": p.pid,
                "url": URL,
                "stdout": str(stdout),
                "stderr": str(stderr),
                "status": status
            }
        time.sleep(1)

    return {
        "result": "starting",
        "pid": p.pid,
        "url": URL,
        "stdout": str(stdout),
        "stderr": str(stderr),
        "note": "ComfyUI is still warming up. Run /comfy-status."
    }


def stop_comfyui():
    if not PID_FILE.exists():
        return {"result": "no pid file", "url": URL}

    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        PID_FILE.unlink(missing_ok=True)
        return {"result": "bad pid file removed"}

    subprocess.run(["kill", str(pid)], check=False)
    PID_FILE.unlink(missing_ok=True)

    return {"result": "stopped", "pid": pid, "url": URL}


def pick_checkpoint():
    ckpt_dir = COMFY / "models" / "checkpoints"
    ckpts = sorted(ckpt_dir.glob("*.safetensors"))

    if not ckpts:
        raise RuntimeError("No .safetensors checkpoint found in ComfyUI/models/checkpoints")

    return ckpts[0].name


def workflow(prompt, width=768, height=768, steps=4, cfg=1.0, seed=None):
    seed = int(seed if seed is not None else random.randint(1, 2**31 - 1))
    ckpt = pick_checkpoint()

    negative = (
        "random text, watermark, logo, malformed anatomy, duplicate features, blurry, low quality, "
        "extra limbs, bad hands, bad eyes, distorted face"
    )

    return {
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": ckpt}
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["4", 1]}
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["4", 1]}
        },
        "7": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": int(width), "height": int(height), "batch_size": 1}
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": int(steps),
                "cfg": float(cfg),
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["5", 0],
                "negative": ["6", 0],
                "latent_image": ["7", 0]
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"images": ["8", 0], "filename_prefix": "Titan_Comfy"}
        }
    }


def download_view(filename, subfolder="", folder_type="output"):
    query = urllib.parse.urlencode({
        "filename": filename,
        "subfolder": subfolder,
        "type": folder_type,
    })

    raw = api_get("/view?" + query, timeout=60)
    out = OUT / f"{now()}_{filename}"
    out.write_bytes(raw)
    return out


def comfy_image(prompt, width=768, height=768, steps=4, cfg=1.0):
    status = comfy_status()

    if not status.get("running"):
        started = start_comfyui()
        status = comfy_status()

        if not status.get("running"):
            return {
                "error": "ComfyUI is not running.",
                "start_attempt": started,
                "status": status
            }

    wf = workflow(prompt, width=width, height=height, steps=steps, cfg=cfg)
    res = api_post("/prompt", {"prompt": wf}, timeout=30)
    prompt_id = res["prompt_id"]

    for _ in range(240):
        hist = api_json("/history/" + prompt_id, timeout=10)

        if prompt_id in hist:
            outputs = hist[prompt_id].get("outputs", {})

            for node in outputs.values():
                for img in node.get("images", []):
                    path = download_view(
                        img["filename"],
                        img.get("subfolder", ""),
                        img.get("type", "output"),
                    )

                    subprocess.Popen(["open", str(path)])

                    return {
                        "result": "image created",
                        "backend": "comfyui-local",
                        "path": str(path),
                        "prompt": prompt,
                        "checkpoint": pick_checkpoint(),
                        "url": URL
                    }

        time.sleep(1)

    return {"error": "Timed out waiting for image.", "prompt_id": prompt_id}


def comfy_info():
    return comfy_status()
