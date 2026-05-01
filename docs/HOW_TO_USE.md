# TitanAgent — How to Use

## Quick Start

```bash
cd /Volumes/AI_DRIVE/TitanAgent
source venv/bin/activate
python3 titan_terminal.py
```

Dashboard runs at `http://127.0.0.1:5050` — launch it with `/dashboard` or:

```bash
python3 launch_dashboard.py
```

---

## Terminal Commands

Type `/` in the terminal to see all 77 commands. Tab-complete works on any command.

### Core

| Command | What it does |
|---------|-------------|
| `/help` | Show all commands |
| `/doctor` | Check folders and config |
| `/models` | Show current model config |
| `/exit` | Quit Titan |
| `/tree` | Show workspace file tree |

### Model Profiles (switch models instantly)

| Command | Model | Speed |
|---------|-------|-------|
| `/tiny` | qwen3:1.7b | Fastest |
| `/fast` | qwen2.5-coder:7b | Fast |
| `/coder` | qwen2.5-coder:14b | Medium |
| `/smart` | qwen3:8b | Medium |
| `/heavy` | qwen3.6-35b:iq3 | Slow |
| `/max` | qwen3.6:35b | Slowest |

### Images & Video

| Command | What it does |
|---------|-------------|
| `/image <prompt>` | Generate an image |
| `/gif <prompt>` | Generate a GIF |
| `/images` | List generated images |
| `/image-backend <backend>` | Set backend: `pollinations`, `comfyui`, `local` |
| `/image-enhance <on\|off>` | Toggle prompt enhancement |
| `/video <prompt>` | Generate a video |
| `/videos` | List generated videos |
| `/video-status` | Show video config |
| `/video-quality <low\|medium\|high>` | Set video quality |
| `/video-motion <low\|medium\|high>` | Set video motion amount |
| `/upscale <file> [scale]` | Upscale an image |
| `/porn <prompt>` | Generate explicit content |

### ComfyUI (Local Stable Diffusion)

| Command | What it does |
|---------|-------------|
| `/comfy-status` | Check if ComfyUI is running |
| `/comfy-start` | Start ComfyUI server |
| `/comfy-stop` | Stop ComfyUI server |
| `/comfy-image <prompt>` | Generate image via ComfyUI directly |

### Products (Scaffold Projects)

| Command | What it does |
|---------|-------------|
| `/products` | List all products |
| `/product-create <name>` | Create a product |
| `/product-template <kind>` | Create from template |
| `/product-start <name>` | Start a product |
| `/product-stop <name>` | Stop a product |
| `/product-logs <name>` | Show product logs |
| `/templates` | List available templates |

6 templates: `python_cli`, `flask_app`, `static_website`, `api_service`, `flask_dashboard`, `landing_page`

### Skills & Agents

| Command | What it does |
|---------|-------------|
| `/skills` | List skill packs |
| `/skill-create <name>` | Create a new skill pack |
| `/skill <name> <task>` | Run a skill |
| `/pip <package>` | Install a Python package |
| `/agents` | Show available subagents |
| `/team <task>` | Run a team task (planner → coder → tester → reviewer) |

### Memory & RAG

| Command | What it does |
|---------|-------------|
| `/memory` | Show saved memories |
| `/remember <text>` | Save a memory |
| `/recall <query>` | Search memories |
| `/forget <id>` | Delete a memory |
| `/rag` | Show RAG status |
| `/rag-index` | Index documents for search |
| `/rag-search <query>` | Search indexed documents |

### Search & Files

| Command | What it does |
|---------|-------------|
| `/search <query>` | Search workspace files |
| `/snapshot` | Save a workspace snapshot |
| `/changed` | Show files changed since last snapshot |
| `/diff <path>` | Show diff of a changed file |

### Web

| Command | What it does |
|---------|-------------|
| `/web <query>` | Search the web |
| `/fetch <url>` | Fetch a URL's content |
| `/download <url>` | Download a file from URL |

### Idea Chat (brainstorm with Titan)

| Command | What it does |
|---------|-------------|
| `/idea <text>` | Sharpen an idea |
| `/brainstorm <text>` | Rapid-fire diverse directions |
| `/critic <text>` | Tear it apart constructively |
| `/builder <text>` | Turn idea into concrete steps |
| `/simple <text>` | Explain in plain language |
| `/idea-model <model>` | Set which model idea chat uses |

### Permissions

| Command | What it does |
|---------|-------------|
| `/mode` | Show current permission mode |
| `/safe` | Read-only mode |
| `/power` | Workspace read/write mode |
| `/agentic` | Full autonomous mode |

### Jobs (Background Tasks)

| Command | What it does |
|---------|-------------|
| `/bg <task>` | Start a background job |
| `/jobs` | List running jobs |
| `/job <id>` | Show job details |
| `/trace-job <id>` | Show job trace |
| `/cancel <id>` | Cancel a running job |

---

## Dashboard

Open `http://127.0.0.1:5050` in your browser. 16 tabs:

| Tab | What it does |
|-----|-------------|
| 💬 Chat | Natural language chat with Titan (type anything) |
| ▣ Video | Create and configure videos |
| 🖼 Images | Create images/GIFs, switch backends, toggle enhancement |
| ⬡ ComfyUI | Start/stop ComfyUI, generate images locally |
| ▤ History | Browse chat history sections |
| ▣ Jobs | Monitor background jobs and traces |
| 🗂 Files | Browse and edit workspace files |
| 🔎 Search / Diff | Search files, view snapshots and diffs |
| ◇ Products | Create and manage products |
| ✧ Skills | List and create skill packs |
| ⇶ Agents | View subagents, run team tasks |
| 🧠 Memory | Save, search, and delete memories |
| ⌕ RAG | Index and search documents |
| ☷ Models | Switch model profiles |
| ⚙ Permissions | Set permission mode |
| 🔥 NSFW | Explicit content studio (toggle NSFW, create images/GIFs/videos) |

### Keyboard Shortcuts

- **Ctrl+K** (or Cmd+K on Mac) — Open command palette
- **Escape** — Close command palette
- **↑↓** — Navigate palette commands
- **Enter** — Run selected command

---

## Natural Language

Just type anything (no slash command needed) and Titan will:

1. Check if it matches a media request (image, video, GIF)
2. Try fast shortcuts (workspace tree, list files, etc.)
3. Fall back to the full agent loop (Ollama model with tool access)

Examples:
```
show me the workspace tree
create an image of a sunset over mountains
search RAG for dashboard port
list my products
what files changed recently
```

---

## Image Generation Backends

Titan tries backends in order. If one fails, it falls back automatically.

### Pollinations (default — cloud, no GPU needed)

```
/image-backend pollinations
```

- Free, no setup required
- Decent quality, ~10-30 seconds per image
- Works offline? No

### ComfyUI (local — best quality)

```
/comfy-start
/image-backend comfyui
/comfy-image beautiful woman in a red dress
```

- Requires local GPU with SD/Pony model installed
- Highest quality, unlimited generation
- Works offline? Yes

Setup: see `docs/nsfw_lora_guide.md`

### Local Pillow fallback

```
/image-backend local
```

- Always works, no GPU needed
- Generates geometric patterns only
- Use only as last resort

---

## Config

Edit `config.json` to change settings:

```json
{
  "model": "qwen2.5-coder:7b",
  "fallback_model": "qwen3:8b",
  "image_backend": "pollinations",
  "image_enhance_prompt": true,
  "nsfw_enabled": true,
  "allow_nsfw": true,
  "video_quality": "high",
  "video_fps": 30,
  "comfy_steps": 4,
  "comfy_cfg": 1.0,
  "permission_mode": "power"
}
```

---

## File Locations

| Item | Path |
|------|------|
| Generated images | `downloads/images/` |
| NSFW images | `downloads/porn/` |
| Generated videos | `downloads/videos/` |
| Workspace files | `workspace/` |
| Products | `products/` |
| Skills | `skills/` |
| Chat history | `memory/chat_history/` |
| Config | `config.json` |
| ComfyUI | `local_ai/ComfyUI/` |
| SD models | `local_ai/ComfyUI/models/checkpoints/` |
| LoRAs | `local_ai/ComfyUI/models/loras/` |
| Setup guide | `docs/nsfw_lora_guide.md` |