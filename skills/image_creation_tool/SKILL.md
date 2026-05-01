# image_creation_tool

Create images and GIFs using Titan's media pipeline (ComfyUI → Pollinations → Local Pillow).

## When to use

When the user wants to generate, list, or configure images/GIFs.

## Workflow

1. Check current image backend: `read_file config.json` → look for `image_backend` field.
2. For creation: call `create_image` with a prompt string. Width/height default to 768x768.
3. For GIFs: call `create_gif` — requires a prompt, frames default to 28.
4. The pipeline tries backends in order: comfyui → pollinations → local (Pillow).
5. If ComfyUI fails, it falls back automatically. No need to check status first.
6. Images save to `downloads/images/`. GIFs save to the same folder.
7. Use `list_images` to show recent files. Use `set_image_backend` to switch backends.
8. For NSFW: `config.json` must have `nsfw_enabled: true`. Then `create_image(..., nsfw=True)` uses the NSFW output folder.

## Backend details

- **comfyui**: Sends a KSampler workflow to `http://127.0.0.1:8188`. Requires a checkpoint in `local_ai/ComfyUI/models/checkpoints/`. Slow but high quality.
- **pollinations**: Hits `https://image.pollinations.ai/prompt/...`. Fast, decent quality, no local GPU needed.
- **local**: Generates a simple geometric pattern with Pillow. Always works, low quality.

## Enhancement

When `image_enhance` is "on" in config, prompts are expanded with quality/style modifiers before generation.

## Dependencies

- Pillow (for local fallback)
- ComfyUI (optional, for SD generation)

## Notes

Image generation can take 30s-3min depending on backend. Always tell the user it's processing.