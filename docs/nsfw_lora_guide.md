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

---

## NSFW / LoRA Setup Guide (May 2026)

TitanAgent supports NSFW generation when `nsfw_enabled: true` is set in `config.json`. Use `/porn <prompt>` from the terminal or the NSFW Studio tab in the dashboard.

### Top 5 LoRAs for Realistic Explicit Content

| Rank | LoRA Name | Best For | Trigger Word | Strength | Priority |
|------|-----------|----------|--------------|----------|----------|
| 1 | Realistic Skin Texture | Ultra-realistic skin, pores, details | `realistic skin` | 0.8–1.0 | Must Have |
| 2 | Perfect Anatomy XL | Better hands, anatomy, proportions | `perfect anatomy` | 0.7–0.9 | Must Have |
| 3 | Detailed Pussy & Ass | Highly detailed genitals | `detailed pussy` | 0.6–0.85 | High |
| 4 | Ahegao / Aroused Face | Best facial expressions | `ahegao` or `aroused face` | 0.7–1.0 | High |
| 5 | Cum & Fluids | Realistic cum, wetness, creampie | `cum on body` | 0.6–0.8 | Medium |

**Best combination**: Use LoRA #1 + #2 together for the biggest quality jump.

### Step 1: Download the LoRAs

1. Go to CivitAI.com
2. Search and download these LoRAs (sort by "Most Downloaded" or "Highest Rated"):
   - Search: `Realistic Skin Texture SDXL` or `Pony`
   - Search: `Perfect Anatomy XL` or `Better Hands SDXL`
   - Search: `Detailed Pussy LoRA` (Pony or SDXL version)
3. Download the `.safetensors` files

### Step 2: Install the LoRAs

1. Place all downloaded `.safetensors` files into:
   ```
   C:\stable-diffusion-webui\models\Lora\
   ```
2. In your browser, click the refresh icon next to the LoRA section (below the prompt box)

### Step 3: Use LoRAs in Prompts

Add trigger words and LoRA references to your prompt using this syntax:

```
<lora:FileName:Strength>
```

**Full prompt template:**

```
score_9, score_8_up, score_7_up, masterpiece, best quality, 8k, photorealistic,

beautiful 25 year old woman, perfect anatomy, realistic skin, detailed skin texture, large natural breasts, slim waist, long hair, seductive expression, aroused face,

standing in bedroom, black lace lingerie, legs slightly spread, detailed pussy, aroused, wet,

<lora:Realistic_Skin_Texture:0.85>, <lora:Perfect_Anatomy_XL:0.75>, <lora:Detailed_Pussy:0.7>
```

The number (0.7, 0.85, etc.) controls how strong the LoRA effect is. Start with 0.7–0.85 and adjust.

### Recommended Settings with LoRAs

| Setting | Value |
|---------|-------|
| Sampling Steps | 30–40 |
| CFG Scale | 5–7 |
| Resolution | 768x1152 or 832x1216 |
| Sampler | Euler a or DPM++ 2M Karras |
| Hires. fix | Enabled (1.5x, 15–20 steps) |
| ADetailer | Enabled (for face + hands) |

### Using LoRAs with TitanAgent

Titan's ComfyUI bridge supports LoRAs when ComfyUI is running locally:

1. Start ComfyUI: `/comfy-start` in terminal
2. Set backend: `/image-backend comfyui`
3. Generate: `/porn <your prompt with lora tags>`
4. Or use the NSFW Studio tab in the dashboard

For Automatic1111, LoRAs work automatically once placed in the `models/Lora/` folder.

### Prompting Tips for Explicit Content

1. **Be specific about style first**: "photograph, 8k, photorealistic"
2. **Describe the subject clearly**: Use anatomical terminology for better results
3. **Add quality modifiers**: "highly detailed, sharp focus, studio lighting"
4. **Use negative prompts**: Titan adds default negatives, but you can add more
5. **Lighting matters**: "dramatic lighting, rim lighting, golden hour" improves quality significantly
6. **Some models have NSFW filters**: Use models tagged "unfiltered" or "NSFW" on CivitAI
7. **ComfyUI has no built-in content filter**: Works out of the box for NSFW
8. **Automatic1111**: Requires `--no-half-vae` flag and an unfiltered model

### Agent Instruction (Copy-Paste Ready)

```
Set up the best realistic porn generation using Automatic1111 + LoRAs.

Install these exact LoRAs: Realistic Skin Texture, Perfect Anatomy XL, Detailed Pussy.
Put them in the Lora folder.
Use this exact prompt template with trigger words at strength 0.75-0.85.
Apply these generation settings: Steps 30-40, CFG 5-7, Resolution 768x1152, Sampler Euler a, Hires fix enabled 1.5x, ADetailer enabled.
Generate 5 test images and tell me which LoRA combination gives the best skin and anatomy.
```

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `/image <prompt>` | Generate an image |
| `/porn <prompt>` | Generate explicit content |
| `/gif <prompt>` | Create short GIF |
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
| NSFW images | `TitanAgent/downloads/porn/` |
| ComfyUI | `TitanAgent/local_ai/ComfyUI/` |
| Config | `TitanAgent/config.json` |
| SD models | `ComfyUI/models/checkpoints/` |
| LoRAs | `ComfyUI/models/loras/` or `stable-diffusion-webui/models/Lora/` |