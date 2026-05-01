# TitanAgent — Beginner Setup Guide

## Stable Diffusion WebUI Setup (Windows)

This guide walks you through installing Stable Diffusion WebUI on Windows so TitanAgent can use it for local image generation.

### Prerequisites

- Windows 10 or 11 (64-bit)
- NVIDIA GPU with at least 4GB VRAM (8GB+ recommended)
- Python 3.10.x (do NOT use 3.11+ or 3.9)
- Git for Windows
- ~10GB free disk space

### Step 1: Install Python 3.10

1. Download Python 3.10 from https://www.python.org/downloads/release/python-3100/
2. Run the installer
3. **Check "Add Python to PATH"** at the bottom of the installer
4. Click "Install Now"
5. Open Command Prompt and verify:
   ```
   python --version
   ```
   Should show `Python 3.10.x`

### Step 2: Install Git

1. Download from https://git-scm.com/download/win
2. Run the installer with default settings
3. Verify:
   ```
   git --version
   ```

### Step 3: Clone Stable Diffusion WebUI

1. Open Command Prompt
2. Navigate to where you want to install:
   ```
   cd C:\
   ```
3. Clone the repo:
   ```
   git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
   ```
4. Enter the directory:
   ```
   cd stable-diffusion-webui
   ```

### Step 4: Download a Model

1. Go to https://civitai.com/ or https://huggingface.co/models?pipeline=text-to-image
2. Download a `.safetensors` or `.ckpt` model file
3. Recommended starter models:
   - **SD 1.5**: Fast, works on 4GB VRAM — search "stable diffusion 1.5" on HuggingFace
   - **SDXL 1.0**: Higher quality, needs 8GB+ VRAM
   - **Anything V5**: Good for anime/art styles
4. Place the model file in:
   ```
   C:\stable-diffusion-webui\models\Stable-diffusion\
   ```

### Step 5: Launch WebUI

1. In the `stable-diffusion-webui` directory, run:
   ```
   webui-user.bat
   ```
2. The first launch takes 5-15 minutes (installs dependencies)
3. When ready, it opens `http://127.0.0.1:7860` in your browser
4. Type a prompt like "a cat sitting on a windowsill, oil painting" and click Generate

### Step 6: Connect to TitanAgent

TitanAgent's ComfyUI bridge works with ComfyUI, not Automatic1111. To use local SD with Titan:

**Option A: ComfyUI (recommended)**

1. Download ComfyUI from https://github.com/comfyanonymous/ComfyUI
2. Extract to `TitanAgent/local_ai/ComfyUI/`
3. Place your checkpoint in `ComfyUI/models/checkpoints/`
4. Start ComfyUI:
   ```
   cd TitanAgent\local_ai\ComfyUI
   python main.py --listen 127.0.0.1 --port 8188
   ```
5. In Titan terminal, use `/comfy-start` or set image backend to comfyui

**Option B: Automatic1111 API**

If you prefer A1111, Titan can call its API. Start with:
```
webui-user.bat --api --listen 127.0.0.1 7860
```
Then use `fetch_url` in Titan to hit `http://127.0.0.1:7860/sdapi/v1/txt2img`.

### Troubleshooting

- **"CUDA out of memory"**: Lower resolution, use `--medvram` or `--lowvram` flag
- **"RuntimeError: Couldn't install torch"**: Install PyTorch manually:
  ```
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
  ```
- **Black images**: Update to latest WebUI version (`git pull`)
- **Slow generation**: Check GPU utilization in Task Manager — if low, reinstall PyTorch with CUDA support
- **"No module named 'xxxx'"**: Run `webui-user.bat` again — it auto-installs missing packages

### Optimizing Generation Settings

| Setting | Fast | Balanced | Quality |
|---------|------|----------|---------|
| Steps | 15 | 25 | 40+ |
| CFG Scale | 7 | 7-12 | 7-12 |
| Resolution | 512x512 | 512x768 | 768x1024 |
| Batch Size | 1 | 1 | 1 |

### NSFW / Uncensored Prompting Guide

TitanAgent supports NSFW generation when `nsfw_enabled: true` is set in `config.json`.

**Prompt construction tips:**

1. **Be specific about style first**: "oil painting, photograph, digital art, watercolor"
2. **Describe the subject clearly**: "woman with red hair", "man in business suit"
3. **Add quality modifiers**: "highly detailed, 8k, sharp focus, studio lighting"
4. **Use negative prompts wisely**: Titan adds default negatives, but you can add more
5. **For explicit content**: Use anatomical terminology rather than euphemisms for better results
6. **Lighting matters**: "dramatic lighting, rim lighting, golden hour" improves quality significantly

**Prompt templates:**

```
[style], [subject], [action/pose], [setting], [lighting], quality modifiers
```

Example:
```
photograph, woman with red hair, sitting on velvet couch, dimly lit room, candlelight, highly detailed, sharp focus, 8k
```

**Important notes:**
- NSFW generation is slower due to higher step counts
- Some SD models have NSFW filters built in — use models tagged "unfiltered" or "NSFW" on CivitAI
- ComfyUI has no built-in content filter; Automatic1111 requires `--no-half-vae` flag
- Always check your model's license before generating commercial content

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `/image <prompt>` | Generate an image |
| `/image-backend pollinations` | Use Pollinations (cloud) |
| `/image-backend comfyui` | Use ComfyUI (local SD) |
| `/image-backend local` | Use Pillow fallback |
| `/comfy-status` | Check ComfyUI connection |
| `/comfy-start` | Start ComfyUI server |
| `/comfy-image <prompt>` | Generate via ComfyUI directly |
| `/image-enhance` | Toggle prompt enhancement |

## File Locations

| Item | Path |
|------|------|
| Generated images | `TitanAgent/downloads/images/` |
| ComfyUI | `TitanAgent/local_ai/ComfyUI/` |
| Config | `TitanAgent/config.json` |
| SD models | `ComfyUI/models/checkpoints/` |