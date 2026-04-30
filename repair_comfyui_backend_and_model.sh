#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
COMFY="$BASE/local_ai/ComfyUI"
MODEL_DIR="$COMFY/models/checkpoints"
MODEL_FILE="$MODEL_DIR/sd_xl_turbo_1.0_fp16.safetensors"

cd "$BASE"

mkdir -p backups logs/comfyui "$MODEL_DIR"

echo "[1/5] Patching missing terminal helper..."

python3 - <<'PY'
from pathlib import Path
import re

path = Path("titan_terminal.py")
text = path.read_text(encoding="utf-8")

backup = Path("backups/titan_terminal_before_comfy_missing_helper_fix.py")
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

helper = r'''
def terminal_set_image_backend_simple(backend):
    try:
        import json
        from pathlib import Path

        cfg_path = Path("config.json")
        cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}

        backend = str(backend or "").strip() or "comfyui"
        cfg["image_backend"] = backend

        if backend == "comfyui":
            cfg["image_width"] = int(cfg.get("image_width", 768))
            cfg["image_height"] = int(cfg.get("image_height", 768))
            cfg["comfy_steps"] = int(cfg.get("comfy_steps", 4))
            cfg["comfy_cfg"] = float(cfg.get("comfy_cfg", 1.0))

        cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

        say_panel(json.dumps({
            "result": "image backend updated",
            "image_backend": cfg["image_backend"],
            "image_width": cfg.get("image_width"),
            "image_height": cfg.get("image_height"),
            "comfy_steps": cfg.get("comfy_steps"),
            "comfy_cfg": cfg.get("comfy_cfg")
        }, indent=2), title="Image Backend", style="green")
    except Exception as e:
        say_panel("Image backend failed: " + repr(e), title="Image Backend", style="red")


'''

if "def terminal_set_image_backend_simple(" not in text:
    text = text.replace("def repl():", helper + "\ndef repl():", 1)

intercept = r'''
            if lower.startswith("/image-backend "):
                terminal_set_image_backend_simple(command.replace("/image-backend ", "", 1).strip())
                continue

'''

if 'lower.startswith("/image-backend ")' not in text and 'lower == "/image-backend comfyui"' not in text:
    repl_start = text.find("def repl():")
    after = text[repl_start:]
    match = re.search(r"\n\s*if\s+lower\b", after)
    if not match:
        raise SystemExit("Could not find command insertion point.")
    pos = repl_start + match.start()
    text = text[:pos] + intercept + text[pos:]

path.write_text(text, encoding="utf-8")
print("patched terminal_set_image_backend_simple")
PY

echo "[2/5] Repairing ComfyUI venv..."

if [ ! -d "$COMFY" ]; then
  git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFY"
fi

cd "$COMFY"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate

python -m pip install -U pip wheel
python -m pip install 'setuptools>=81,<82'
python -m pip install -U torch torchvision torchaudio
python -m pip install -r requirements.txt
python -m pip install -U huggingface_hub pillow requests

echo "[3/5] Downloading SDXL Turbo checkpoint if missing..."

mkdir -p "$MODEL_DIR"

if [ ! -f "$MODEL_FILE" ]; then
  huggingface-cli download stabilityai/sdxl-turbo sd_xl_turbo_1.0_fp16.safetensors \
    --local-dir "$MODEL_DIR" \
    --local-dir-use-symlinks False
fi

echo "[4/5] Rewriting start script..."

cd "$BASE"

cat > scripts/start_comfyui.sh <<'START'
#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
COMFY="$BASE/local_ai/ComfyUI"

cd "$COMFY"
source .venv/bin/activate

python main.py --listen 127.0.0.1 --port 8188
START

chmod +x scripts/start_comfyui.sh

echo "[5/5] Verifying..."

source "$BASE/venv/bin/activate"

python3 -m py_compile titan_terminal.py agent_core/comfyui_bridge.py agent_core/image_tools.py

find "$MODEL_DIR" -maxdepth 1 -type f -name "*.safetensors" -print

echo "Repair complete."
