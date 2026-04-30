from pathlib import Path
import json
import re

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
BACKUPS = BASE / "backups"
BACKUPS.mkdir(exist_ok=True)

# ------------------------------------------------------------
# 1. Start script
# ------------------------------------------------------------
scripts = BASE / "scripts"
scripts.mkdir(exist_ok=True)

(scripts / "start_comfyui.sh").write_text("""#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
COMFY="$BASE/local_ai/ComfyUI"

if [ ! -d "$COMFY" ]; then
  echo "ComfyUI is not installed at: $COMFY"
  echo "Install it first, then run /comfy-start again."
  exit 1
fi

cd "$COMFY"

if [ -d ".venv" ]; then
  source .venv/bin/activate
else
  echo "ComfyUI .venv missing. Install ComfyUI first."
  exit 1
fi

python main.py --listen 127.0.0.1 --port 8188
""", encoding="utf-8")

(scripts / "start_comfyui.sh").chmod(0o755)

# ------------------------------------------------------------
# 2. ComfyUI bridge
# ------------------------------------------------------------
bridge = BASE / "agent_core" / "comfyui_bridge.py"
bridge.parent.mkdir(exist_ok=True)

bridge.write_text(r'''from pathlib import Path
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
''', encoding="utf-8")

# ------------------------------------------------------------
# 3. Patch image_tools.py to route backend comfyui
# ------------------------------------------------------------
image_tools = BASE / "agent_core" / "image_tools.py"

if image_tools.exists():
    text = image_tools.read_text(encoding="utf-8")
    (BACKUPS / "image_tools_before_one_shot_comfy.py").write_text(text, encoding="utf-8")

    if "backend == \"comfyui\"" not in text:
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

        if count:
            image_tools.write_text(new_text, encoding="utf-8")
        else:
            print("WARN: could not patch create_image in image_tools.py")
else:
    print("WARN: agent_core/image_tools.py not found. /comfy-image will still work.")

# ------------------------------------------------------------
# 4. Config defaults
# ------------------------------------------------------------
cfg_path = BASE / "config.json"
cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}

cfg["image_backend"] = "comfyui"
cfg["image_width"] = int(cfg.get("image_width", 768))
cfg["image_height"] = int(cfg.get("image_height", 768))
cfg["comfy_steps"] = int(cfg.get("comfy_steps", 4))
cfg["comfy_cfg"] = float(cfg.get("comfy_cfg", 1.0))

cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

# ------------------------------------------------------------
# 5. Terminal patch
# ------------------------------------------------------------
term = BASE / "titan_terminal.py"
text = term.read_text(encoding="utf-8")
(BACKUPS / "titan_terminal_before_one_shot_comfy.py").write_text(text, encoding="utf-8")

helpers = r'''
def terminal_comfy_status():
    try:
        import json
        from agent_core.comfyui_bridge import comfy_info
        say_panel(json.dumps(comfy_info(), indent=2), title="ComfyUI", style="cyan")
    except Exception as e:
        say_panel("ComfyUI status failed: " + repr(e), title="ComfyUI", style="red")


def terminal_comfy_start():
    try:
        import json
        from agent_core.comfyui_bridge import start_comfyui
        say_panel(json.dumps(start_comfyui(), indent=2), title="ComfyUI Start", style="green")
    except Exception as e:
        say_panel("ComfyUI start failed: " + repr(e), title="ComfyUI", style="red")


def terminal_comfy_stop():
    try:
        import json
        from agent_core.comfyui_bridge import stop_comfyui
        say_panel(json.dumps(stop_comfyui(), indent=2), title="ComfyUI Stop", style="yellow")
    except Exception as e:
        say_panel("ComfyUI stop failed: " + repr(e), title="ComfyUI", style="red")


def terminal_comfy_image(args):
    try:
        import json
        from agent_core.comfyui_bridge import comfy_image

        prompt = str(args or "").strip()

        if not prompt:
            say_panel("Usage: /comfy-image <prompt>", title="ComfyUI Image", style="yellow")
            return

        result = comfy_image(prompt)
        say_panel(json.dumps(result, indent=2), title="ComfyUI Image", style="green")
    except Exception as e:
        say_panel("ComfyUI image failed: " + repr(e), title="ComfyUI Image", style="red")


def terminal_set_image_backend_simple(backend):
    try:
        import json
        from pathlib import Path

        cfg_path = Path("config.json")
        cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
        cfg["image_backend"] = str(backend or "").strip() or "comfyui"
        cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        say_panel(json.dumps({"image_backend": cfg["image_backend"]}, indent=2), title="Image Backend", style="green")
    except Exception as e:
        say_panel("Image backend failed: " + repr(e), title="Image Backend", style="red")


'''

if "def terminal_comfy_status(" not in text:
    text = text.replace("def repl():", helpers + "\ndef repl():", 1)

intercept = r'''
            # TITAN_COMFY_COMMANDS_V1
            if lower == "/comfy-status":
                terminal_comfy_status()
                continue

            if lower == "/comfy-start":
                terminal_comfy_start()
                continue

            if lower == "/comfy-stop":
                terminal_comfy_stop()
                continue

            if lower.startswith("/comfy-image "):
                terminal_comfy_image(command.replace("/comfy-image ", "", 1).strip())
                continue

            if lower == "/image-backend comfyui":
                terminal_set_image_backend_simple("comfyui")
                continue

'''

if "TITAN_COMFY_COMMANDS_V1" not in text:
    repl_start = text.find("def repl():")

    if repl_start == -1:
        raise SystemExit("Could not find def repl() in titan_terminal.py")

    after = text[repl_start:]
    match = re.search(r"\n\s*if\s+lower\b", after)

    if not match:
        raise SystemExit("Could not find command handler insertion point in repl()")

    pos = repl_start + match.start()
    text = text[:pos] + intercept + text[pos:]

# ------------------------------------------------------------
# 6. Multi-line paste queue
# ------------------------------------------------------------
queue_code = r'''
# TITAN_MULTILINE_QUEUE_V1
_titan_command_queue = []

def titan_next_command(prompt_text):
    global _titan_command_queue

    if _titan_command_queue:
        return _titan_command_queue.pop(0)

    if "titan_prompt_input" in globals():
        raw = titan_prompt_input(prompt_text)
    else:
        raw = input(prompt_text)

    raw = str(raw or "").replace("\r\n", "\n").replace("\r", "\n")
    parts = [line.strip() for line in raw.split("\n") if line.strip()]

    if not parts:
        return ""

    if len(parts) > 1:
        _titan_command_queue.extend(parts[1:])

    return parts[0]

'''

if "TITAN_MULTILINE_QUEUE_V1" not in text:
    text = text.replace("def repl():", queue_code + "\ndef repl():", 1)

replace_patterns = [
    (r"command\s*=\s*titan_prompt_input\(([^)]*)\)", r"command = titan_next_command(\1)"),
    (r"user_input\s*=\s*titan_prompt_input\(([^)]*)\)", r"user_input = titan_next_command(\1)"),
    (r"command\s*=\s*input\(([^)]*)\)", r"command = titan_next_command(\1)"),
    (r"user_input\s*=\s*input\(([^)]*)\)", r"user_input = titan_next_command(\1)"),
]

for pattern, replacement in replace_patterns:
    text = re.sub(pattern, replacement, text)

term.write_text(text, encoding="utf-8")

print("One-shot ComfyUI command patch complete.")
print("Installed: /comfy-start /comfy-status /comfy-stop /comfy-image")
print("Image backend set to comfyui.")
print("Multi-line paste support installed.")
