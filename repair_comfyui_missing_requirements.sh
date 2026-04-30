#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
COMFY="$BASE/local_ai/ComfyUI"
BACKUP="$BASE/local_ai/ComfyUI_broken_$(date +%Y%m%d_%H%M%S)"
MODEL_DIR="$COMFY/models/checkpoints"
MODEL_FILE="$MODEL_DIR/sd_xl_turbo_1.0_fp16.safetensors"

cd "$BASE"

mkdir -p local_ai logs/comfyui scripts

if [ -d "$COMFY" ] && [ ! -f "$COMFY/requirements.txt" ]; then
  echo "Broken ComfyUI folder found. Moving to:"
  echo "$BACKUP"
  mv "$COMFY" "$BACKUP"
fi

if [ ! -d "$COMFY/.git" ]; then
  git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFY"
else
  cd "$COMFY"
  git pull
fi

cd "$COMFY"

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -U pip wheel
python -m pip install 'setuptools>=81,<82'
python -m pip install -U torch torchvision torchaudio
python -m pip install -r requirements.txt
python -m pip install -U huggingface_hub pillow requests

mkdir -p "$MODEL_DIR"

if [ ! -f "$MODEL_FILE" ]; then
  huggingface-cli download stabilityai/sdxl-turbo sd_xl_turbo_1.0_fp16.safetensors \
    --local-dir "$MODEL_DIR" \
    --local-dir-use-symlinks False
fi

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

source "$BASE/venv/bin/activate"

python3 - <<'PY'
from pathlib import Path
import json

cfg_path = Path("config.json")
cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}

cfg["image_backend"] = "comfyui"
cfg["image_width"] = 768
cfg["image_height"] = 768
cfg["comfy_steps"] = 4
cfg["comfy_cfg"] = 1.0

cfg_path.write_text(json.dumps(cfg, indent=2))
print("Titan image backend set to ComfyUI.")
PY

python3 -m py_compile titan_terminal.py agent_core/comfyui_bridge.py agent_core/image_tools.py

echo ""
echo "ComfyUI repair complete."
echo "Model files:"
find "$MODEL_DIR" -maxdepth 1 -type f -name "*.safetensors" -print
