#!/usr/bin/env bash
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
