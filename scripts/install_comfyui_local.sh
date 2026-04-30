#!/usr/bin/env bash
set -euo pipefail

BASE="/Volumes/AI_DRIVE/TitanAgent"
COMFY="$BASE/local_ai/ComfyUI"
MODEL_DIR="$COMFY/models/checkpoints"
MODEL_FILE="$MODEL_DIR/sd_xl_turbo_1.0_fp16.safetensors"

cd "$BASE"
mkdir -p local_ai downloads/images logs/comfyui "$MODEL_DIR"

if ! command -v git >/dev/null 2>&1; then
  xcode-select --install || true
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

if [ ! -f "$MODEL_FILE" ]; then
  huggingface-cli download stabilityai/sdxl-turbo sd_xl_turbo_1.0_fp16.safetensors \
    --local-dir "$MODEL_DIR" \
    --local-dir-use-symlinks False
fi

echo "ComfyUI local install complete."
echo "Model: $MODEL_FILE"
