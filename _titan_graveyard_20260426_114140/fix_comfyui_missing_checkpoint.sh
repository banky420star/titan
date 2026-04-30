#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
COMFY="$BASE/local_ai/ComfyUI"
MODEL_DIR="$COMFY/models/checkpoints"
MODEL_FILE="$MODEL_DIR/sd_xl_turbo_1.0_fp16.safetensors"

mkdir -p "$MODEL_DIR"

echo "[1/5] Searching for existing .safetensors files..."
FOUND="$(find "$BASE" -type f -name "*.safetensors" 2>/dev/null | head -n 1 || true)"

if [ -n "$FOUND" ]; then
  echo "Found model:"
  echo "$FOUND"

  if [ "$FOUND" != "$MODEL_FILE" ]; then
    echo "Copying model into ComfyUI checkpoints..."
    cp "$FOUND" "$MODEL_FILE"
  fi
else
  echo "No local .safetensors model found."
fi

echo "[2/5] Checking checkpoint folder..."
find "$MODEL_DIR" -maxdepth 2 -type f -name "*.safetensors" -print || true

if ! find "$MODEL_DIR" -maxdepth 2 -type f -name "*.safetensors" | grep -q .; then
  echo "[3/5] Downloading SDXL Turbo checkpoint..."

  if [ ! -d "$COMFY/.venv" ]; then
    cd "$COMFY"
    python3 -m venv .venv
  fi

  cd "$COMFY"
  source .venv/bin/activate

  python -m pip install -U pip wheel
python -m pip install 'setuptools>=81,<82' huggingface_hub requests

  python - <<'PY'
from pathlib import Path
from huggingface_hub import hf_hub_download

model_dir = Path("/Volumes/AI_DRIVE/TitanAgent/local_ai/ComfyUI/models/checkpoints")
model_dir.mkdir(parents=True, exist_ok=True)

path = hf_hub_download(
    repo_id="stabilityai/sdxl-turbo",
    filename="sd_xl_turbo_1.0_fp16.safetensors",
    local_dir=str(model_dir),
)

print("Downloaded:", path)
PY
else
  echo "[3/5] Checkpoint already exists."
fi

echo "[4/5] Patching ComfyUI bridge to find nested checkpoints..."

cd "$BASE"
source venv/bin/activate

python3 - <<'PY'
from pathlib import Path
import re

path = Path("agent_core/comfyui_bridge.py")
text = path.read_text(encoding="utf-8")

backup = Path("backups/comfyui_bridge_before_checkpoint_recursive_fix.py")
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

text = re.sub(
r'''def checkpoints\(\):
    d = COMFY / "models" / "checkpoints"
    files = \[\]
    for p in sorted\(d.glob\("\*.safetensors"\)\):
        files.append\(p.name\)
    return files''',
r'''def checkpoints():
    d = COMFY / "models" / "checkpoints"
    files = []
    for p in sorted(d.rglob("*.safetensors")):
        files.append(str(p.relative_to(d)))
    return files''',
text,
flags=re.S
)

text = re.sub(
r'''def pick_checkpoint\(\):
    ckpts = checkpoints\(\)
    if not ckpts:
        raise RuntimeError\("No checkpoint found in local_ai/ComfyUI/models/checkpoints"\)
    return ckpts\[0\]''',
r'''def pick_checkpoint():
    ckpts = checkpoints()
    if not ckpts:
        raise RuntimeError("No .safetensors checkpoint found in ComfyUI/models/checkpoints")
    return ckpts[0]''',
text,
flags=re.S
)

path.write_text(text, encoding="utf-8")
print("Patched recursive checkpoint discovery.")
PY

echo "[5/5] Verifying..."
python3 -m py_compile agent_core/comfyui_bridge.py agent_core/image_tools.py titan_terminal.py

echo ""
echo "Checkpoint files:"
find "$MODEL_DIR" -maxdepth 2 -type f -name "*.safetensors" -print

echo ""
echo "Done."
