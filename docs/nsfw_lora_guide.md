# TitanAgent — SD Setup & Pony Diffusion XL Guide

## Stable Diffusion WebUI Setup (Windows)

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

### Step 4: Download Pony Diffusion V6 XL

1. Go to CivitAI and search for **Pony Diffusion V6 XL**
2. Download the `.safetensors` file
3. Place it in:
   ```
   C:\stable-diffusion-webui\models\Stable-diffusion\
   ```
4. This is the **primary model** — select it from the Checkpoint dropdown at the top of the UI

### Step 5: Launch WebUI

1. In the `stable-diffusion-webui` directory, run:
   ```
   webui-user.bat
   ```
2. The first launch takes 5-15 minutes (installs dependencies)
3. When ready, it opens `http://127.0.0.1:7860` in your browser

### Step 6: Connect to TitanAgent

**Option A: ComfyUI (recommended)**

1. Download ComfyUI from https://github.com/comfyanonymous/ComfyUI
2. Extract to `TitanAgent/local_ai/ComfyUI/`
3. Place Pony Diffusion V6 XL checkpoint in `ComfyUI/models/checkpoints/`
4. Start ComfyUI:
   ```
   cd TitanAgent\local_ai\ComfyUI
   python main.py --listen 127.0.0.1 --port 8188
   ```
5. In Titan terminal, use `/comfy-start` or set image backend to comfyui

**Option B: Automatic1111 API**

Start with:
```
webui-user.bat --api --no-half-vae --listen 127.0.0.1 7860
```
Then use `fetch_url` in Titan to hit `http://127.0.0.1:7860/sdapi/v1/txt2img`.

---

## Pony Diffusion V6 XL — NSFW LoRA Guide

TitanAgent supports NSFW generation when `nsfw_enabled: true` is set in `config.json`. Use `/porn <prompt>` from the terminal or the NSFW Studio tab in the dashboard.

### ⚠️ Step 1: Select the Right Model

In Automatic1111, the **Checkpoint dropdown** at the top must show **Pony Diffusion V6 XL** — not the default SD 1.5 or SDXL model. If it's not in the dropdown, you haven't placed it in the right folder yet.

### Top 5 LoRAs for Realistic Explicit Content (Pony XL)

| Rank | LoRA Name | Best For | Trigger Word | Strength | Priority |
|------|-----------|----------|--------------|----------|----------|
| 1 | Realistic Skin Texture | Ultra-realistic skin, pores, details | `realistic skin` | 0.8–1.0 | Must Have |
| 2 | Perfect Anatomy XL | Better hands, anatomy, proportions | `perfect anatomy` | 0.7–0.9 | Must Have |
| 3 | Detailed Pussy & Ass | Highly detailed genitals | `detailed pussy` | 0.6–0.85 | High |
| 4 | Ahegao / Aroused Face | Best facial expressions | `ahegao` or `aroused face` | 0.7–1.0 | High |
| 5 | Cum & Fluids | Realistic cum, wetness, creampie | `cum on body` | 0.6–0.8 | Medium |

**Best combination**: Use LoRA #1 + #2 together for the biggest quality jump.

### Step 2: Download the LoRAs

1. Go to CivitAI.com
2. Search and download these LoRAs (sort by "Most Downloaded" or "Highest Rated"):
   - Search: `Realistic Skin Texture` (get the Pony or SDXL version)
   - Search: `Perfect Anatomy XL` or `Better Hands SDXL`
   - Search: `Detailed Pussy LoRA` (Pony or SDXL version)
3. Download the `.safetensors` files

### Step 3: Install the LoRAs

1. Place all downloaded `.safetensors` files into:
   ```
   C:\stable-diffusion-webui\models\Lora\
   ```
2. In your browser, click the refresh icon next to the LoRA section (below the prompt box)

### Step 4: Exact Pony XL Prompt (Copy-Paste Ready)

**Positive Prompt:**

```
score_9, score_8_up, score_7_up, source_anime, 

beautiful 25 year old woman, perfect anatomy, realistic skin, detailed skin texture, large natural breasts, slim waist, long hair, seductive expression, aroused face, 

standing in bedroom, black lace lingerie, legs slightly spread, detailed pussy, aroused, wet, 

<lora:Realistic_Skin_Texture:0.8>, <lora:Perfect_Anatomy_XL:0.7>
```

**Negative Prompt:**

```
score_6, score_5, score_4, low quality, bad anatomy, extra limbs, blurry, deformed, watermark, text, censored, child, young, poorly drawn hands, mutation, ugly
```

### Step 5: Generation Settings

| Setting | Value |
|---------|-------|
| **Checkpoint** | Pony Diffusion V6 XL |
| **Sampling method** | Euler a |
| **Sampling steps** | 30 |
| **CFG Scale** | 5 |
| **Resolution** | 768 × 1152 |
| **Hires. fix** | Enabled |
| **Hires upscaler** | 4x-UltraSharp or Latent |
| **Hires steps** | 15 |
| **Hires denoising** | 0.35 |

### Testing — Do This First

Before adding LoRAs, test with the base Pony model:

1. Select **Pony Diffusion V6 XL** in the checkpoint dropdown
2. Remove all `<lora:...>` lines from the prompt
3. Use the positive and negative prompts above
4. Click Generate

If you get random pages or garbage, check:
- Is Pony Diffusion V6 XL actually selected in the dropdown?
- Are LoRA files in `models/Lora/` (not `models/Stable-diffusion/`)?

### Troubleshooting

- **"CUDA out of memory"**: Lower resolution, use `--medvram` or `--lowvram` flag
- **Random/garbage output**: Make sure Pony Diffusion V6 XL is selected, not SD 1.5
- **LoRA not taking effect**: Click the refresh icon next to the LoRA section after adding files
- **Black images**: Add `--no-half-vae` to your WebUI launch args
- **Hands look bad**: Increase Perfect Anatomy XL strength to 0.8–0.9
- **Skin looks plastic**: Increase Realistic Skin Texture to 0.85–1.0
- **"No module named 'xxxx'"**: Run `webui-user.bat` again — it auto-installs missing packages

### Using LoRAs with TitanAgent

Titan's ComfyUI bridge supports LoRAs when ComfyUI is running locally:

1. Start ComfyUI: `/comfy-start` in terminal
2. Set backend: `/image-backend comfyui`
3. Generate: `/porn <your prompt with lora tags>`
4. Or use the NSFW Studio tab in the dashboard

For Automatic1111, LoRAs work automatically once placed in the `models/Lora/` folder.

### Agent Instruction (Copy-Paste Ready)

```
Set up the best realistic porn generation using Automatic1111 + Pony Diffusion V6 XL + LoRAs.

1. Select Pony Diffusion V6 XL as the checkpoint (NOT SD 1.5 or SDXL)
2. Install these LoRAs: Realistic Skin Texture, Perfect Anatomy XL, Detailed Pussy
3. Put them in the Lora folder (NOT the Stable-diffusion folder)
4. Use this EXACT positive prompt with Pony score tags and LoRA syntax at strength 0.7-0.85
5. Use this negative prompt with score_6, score_5, score_4 tags
6. Settings: Euler a, 30 steps, CFG 5, 768x1152, Hires fix ON (4x-UltraSharp, 15 steps, 0.35 denoise)
7. Generate 5 test images WITHOUT LoRAs first to confirm the model works
8. Then add LoRAs one at a time and compare quality
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