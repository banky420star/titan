"""Unified media engine for Titan.

Single entry point for image, video, and GIF generation.
Fallback chain: ComfyUI -> Pollinations -> Local Pillow.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import urllib.request
import ssl

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
CONFIG = BASE / "config.json"
IMAGE_OUT = BASE / "downloads" / "images"
VIDEO_OUT = BASE / "downloads" / "videos"
NSFW_OUT = BASE / "downloads" / "porn"

for d in [IMAGE_OUT, VIDEO_OUT, NSFW_OUT]:
    d.mkdir(parents=True, exist_ok=True)


def load_config():
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


def save_config(cfg):
    CONFIG.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def slug(text):
    text = str(text or "media").lower().strip()
    import re
    text = re.sub(r"[^a-z0-9._-]+", "-", text)
    return text.strip("-")[:70] or "media"


def font(size):
    for p in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/System/Library/Fonts/Supplemental/Verdana.ttf",
    ]:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def clean_prompt(prompt, max_len=1200):
    import re
    prompt = str(prompt or "").strip()
    prompt = re.sub(r"\s+", " ", prompt)
    return prompt[:max_len]


def enhance_prompt(prompt):
    cfg = load_config()
    if not cfg.get("image_enhance_prompt", True):
        return clean_prompt(prompt)
    base = clean_prompt(prompt)
    return (
        base
        + ", highly detailed, visually polished, high quality, professional composition, "
        + "cinematic lighting, clean subject separation, accurate anatomy, sharp focus, "
        + "rich color depth, consistent style, high detail textures, no random text, "
        + "no watermark, no duplicated features, no malformed anatomy, no extra limbs"
    )


def ssl_context():
    cfg = load_config()
    if cfg.get("verify_ssl", True):
        return ssl.create_default_context()
    return ssl._create_unverified_context()


def nsfw_enabled():
    cfg = load_config()
    return cfg.get("nsfw_enabled", False) or cfg.get("allow_nsfw", False)


def output_dir(nsfw=False):
    return NSFW_OUT if nsfw else IMAGE_OUT


# ---------------------------------------------------------------------------
# Backend: Pollinations
# ---------------------------------------------------------------------------

def pollinations_url(prompt, width, height, seed=None):
    seed = seed if seed is not None else abs(hash(prompt)) % 99999999
    encoded = quote(enhance_prompt(prompt))
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={int(width)}&height={int(height)}"
        f"&seed={seed}&nologo=true&enhance=true&model=flux"
    )


def download_image(url, path):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "TitanAgent/1.0",
            "Accept": "image/png,image/jpeg,image/webp,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=120, context=ssl_context()) as response:
        raw = response.read(35_000_000)
    path.write_bytes(raw)
    try:
        img = Image.open(path)
        img.verify()
    except Exception:
        raise RuntimeError("Downloaded file was not a valid image.")
    return path


# ---------------------------------------------------------------------------
# Backend: Local Pillow fallback
# ---------------------------------------------------------------------------

def palette(prompt):
    import random
    seed = sum(ord(c) for c in str(prompt))
    random.seed(seed)
    return random.choice([
        ((17, 18, 20), (232, 171, 67), (221, 134, 123), (255, 243, 161)),
        ((9, 15, 30), (88, 166, 255), (190, 130, 255), (255, 215, 110)),
        ((18, 14, 24), (255, 118, 117), (253, 203, 110), (85, 239, 196)),
        ((10, 22, 20), (46, 204, 113), (241, 196, 15), (230, 126, 34)),
    ])


def draw_titan(draw, x, y, s=1.0, blink=False):
    def rr(a, b, c, d, r, fill):
        draw.rounded_rectangle([x + a * s, y + b * s, x + c * s, y + d * s], radius=r * s, fill=fill)
    rr(0, 42, 28, 86, 10, (246, 224, 100))
    rr(24, 8, 58, 86, 13, (232, 171, 67))
    rr(54, 32, 84, 86, 11, (221, 134, 123))
    eye = (5, 12, 38)
    if blink:
        draw.rounded_rectangle([x + 35 * s, y + 54 * s, x + 49 * s, y + 58 * s], radius=2 * s, fill=eye)
        draw.rounded_rectangle([x + 53 * s, y + 54 * s, x + 67 * s, y + 58 * s], radius=2 * s, fill=eye)
    else:
        draw.ellipse([x + 35 * s, y + 43 * s, x + 49 * s, y + 66 * s], fill=eye)
        draw.ellipse([x + 53 * s, y + 43 * s, x + 67 * s, y + 66 * s], fill=eye)
        draw.ellipse([x + 40 * s, y + 47 * s, x + 44 * s, y + 51 * s], fill=(255, 255, 255))
        draw.ellipse([x + 58 * s, y + 47 * s, x + 62 * s, y + 51 * s], fill=(255, 255, 255))


def local_fallback_image(prompt, width=1024, height=1024):
    import math
    import random
    bg, c1, c2, c3 = palette(prompt)
    random.seed(sum(ord(c) for c in prompt))
    img = Image.new("RGB", (width, height), bg).convert("RGBA")
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(22):
        x = random.randint(-150, width + 150)
        y = random.randint(-150, height + 150)
        r = random.randint(70, 260)
        col = random.choice([c1, c2, c3]) + (random.randint(34, 92),)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    layer = layer.filter(ImageFilter.GaussianBlur(26))
    img = Image.alpha_composite(img, layer)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(
        [80, height - 360, width - 80, height - 80],
        radius=34, fill=(255, 255, 255, 30), outline=(255, 255, 255, 55), width=2,
    )
    draw_titan(d, 120, height - 285, 1.45)
    d.text((250, height - 296), "Titan local fallback", font=font(48), fill=(255, 255, 255, 245))
    y = height - 220
    words = clean_prompt(prompt).split()
    lines, line = [], []
    for word in words:
        if len(" ".join(line + [word])) > 36:
            lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        lines.append(" ".join(line))
    for ln in lines[:6]:
        d.text((250, y), ln, font=font(28), fill=(222, 222, 230, 235))
        y += 40
    return img.convert("RGB")


# ---------------------------------------------------------------------------
# Unified create_image with fallback chain
# ---------------------------------------------------------------------------

def create_image(prompt, width=None, height=None, open_file=True, nsfw=False):
    """Generate an image. Fallback: ComfyUI -> Pollinations -> Local Pillow."""
    cfg = load_config()
    backend = cfg.get("image_backend", "pollinations")
    prompt = clean_prompt(prompt)
    width = int(width or cfg.get("image_width", 768))
    height = int(height or cfg.get("image_height", 768))
    out_dir = output_dir(nsfw=nsfw)
    path = out_dir / f"{stamp()}_{slug(prompt)}.png"
    used_backend = None

    # Try ComfyUI first if configured
    if backend == "comfyui":
        try:
            from agent_core.comfyui_bridge import comfy_image
            result = comfy_image(prompt, width=width, height=height)
            if isinstance(result, dict) and "path" in result:
                if open_file:
                    try:
                        subprocess.Popen(["open", result["path"]])
                    except Exception:
                        pass
                return result
            used_backend = "comfyui"
        except Exception:
            pass  # Fall through to Pollinations

    # Try Pollinations
    try:
        url = pollinations_url(prompt, width, height)
        download_image(url, path)
        used_backend = "pollinations-flux"
    except Exception as poll_err:
        # Final fallback: local Pillow
        img = local_fallback_image(prompt, width, height)
        path = out_dir / f"{stamp()}_{slug(prompt)}_fallback.png"
        img.save(path)
        used_backend = "local-fallback"

    if open_file:
        try:
            subprocess.Popen(["open", str(path)])
        except Exception:
            pass

    return {
        "result": "image created",
        "backend": used_backend,
        "prompt": prompt,
        "path": str(path),
    }


# ---------------------------------------------------------------------------
# GIF generation
# ---------------------------------------------------------------------------

def create_gif(prompt, width=None, height=None, frames=28, open_file=True, nsfw=False):
    import math
    import random
    cfg = load_config()
    width = int(width or cfg.get("gif_width", 768))
    height = int(height or cfg.get("gif_height", 512))
    prompt = clean_prompt(prompt)

    base_result = create_image(prompt, width=width, height=height, open_file=False, nsfw=nsfw)
    base = Image.open(base_result["path"]).convert("RGB").resize((width, height))

    imgs = []
    for i in range(frames):
        t = i / frames
        zoom = 1.0 + 0.035 * math.sin(t * math.tau)
        dx = int(12 * math.sin(t * math.tau))
        dy = int(8 * math.cos(t * math.tau))
        crop_w = int(width / zoom)
        crop_h = int(height / zoom)
        left = max(0, min(width - crop_w, (width - crop_w) // 2 + dx))
        top = max(0, min(height - crop_h, (height - crop_h) // 2 + dy))
        frame = base.crop((left, top, left + crop_w, top + crop_h)).resize((width, height))
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        draw_titan(d, width - 120, height - 138, 1.0, blink=i in [8, 9, 20])
        frame = Image.alpha_composite(frame.convert("RGBA"), overlay).convert(
            "P", palette=Image.Palette.ADAPTIVE
        )
        imgs.append(frame)

    out_dir = NSFW_OUT if nsfw else IMAGE_OUT
    path = out_dir / f"{stamp()}_{slug(prompt)}.gif"
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=80, loop=0)

    if open_file:
        try:
            subprocess.Popen(["open", str(path)])
        except Exception:
            pass

    return {
        "result": "gif created",
        "backend": "animated-generated-image",
        "source_image": base_result["path"],
        "path": str(path),
        "frames": frames,
    }


# ---------------------------------------------------------------------------
# Video generation (keyframe-based animated MP4)
# ---------------------------------------------------------------------------

def create_video(prompt, seconds=None, fps=None, open_file=True, nsfw=False):
    """Generate a video by creating keyframes and assembling into MP4."""
    import math
    import shutil

    cfg = load_config()
    seconds = int(seconds or cfg.get("video_seconds", 8))
    fps = int(fps or cfg.get("video_fps", 24))
    width = int(cfg.get("video_width", 1024))
    height = int(cfg.get("video_height", 576))
    motion = cfg.get("video_motion", "high")
    keyframes = int(cfg.get("video_keyframes", 4))
    out_dir = NSFW_OUT if nsfw else VIDEO_OUT

    prompt = clean_prompt(prompt)
    total_frames = seconds * fps

    # Generate keyframe images
    keyframe_images = []
    for i in range(keyframes):
        seed = abs(hash(f"{prompt}-kf{i}")) % 99999999
        variation = f"{prompt}, frame {i+1} of {keyframes}, cinematic sequence"
        try:
            url = pollinations_url(variation, width, height, seed=seed)
            kf_path = out_dir / f"{stamp()}_{slug(prompt)}_kf{i}.png"
            download_image(url, kf_path)
            keyframe_images.append(kf_path)
        except Exception:
            img = local_fallback_image(variation, width, height)
            kf_path = out_dir / f"{stamp()}_{slug(prompt)}_kf{i}_fallback.png"
            img.save(kf_path)
            keyframe_images.append(kf_path)

    if not keyframe_images:
        return {"error": "Failed to generate any keyframes"}

    # Build frame sequence from keyframes
    import tempfile
    frames_dir = Path(tempfile.mkdtemp(prefix="titan_frames_"))
    frame_idx = 0

    for seg in range(len(keyframe_images) - 1):
        img_a = Image.open(keyframe_images[seg]).convert("RGB").resize((width, height))
        img_b = Image.open(keyframe_images[seg + 1]).convert("RGB").resize((width, height))
        frames_per_seg = total_frames // (len(keyframe_images) - 1)

        for f in range(frames_per_seg):
            t = f / frames_per_seg
            if motion == "high":
                t = t * t * (3 - 2 * t)  # smoothstep
            blended = Image.blend(img_a, img_b, t)
            blended.save(frames_dir / f"frame_{frame_idx:05d}.png")
            frame_idx += 1

    # Pad remaining frames with last keyframe
    last_img = Image.open(keyframe_images[-1]).convert("RGB").resize((width, height))
    while frame_idx < total_frames:
        last_img.save(frames_dir / f"frame_{frame_idx:05d}.png")
        frame_idx += 1

    # Check for ffmpeg
    ffmpeg = shutil.which("ffmpeg")
    video_path = out_dir / f"{stamp()}_{slug(prompt)}.mp4"

    if ffmpeg:
        cmd = [
            ffmpeg, "-y",
            "-framerate", str(fps),
            "-i", str(frames_dir / "frame_%05d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "23",
            str(video_path),
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=300)

        # Clean up temp frames
        import shutil as shutil_mod
        shutil_mod.rmtree(frames_dir, ignore_errors=True)

        if result.returncode == 0 and video_path.exists():
            if open_file:
                try:
                    subprocess.Popen(["open", str(video_path)])
                except Exception:
                    pass
            return {
                "result": "video created",
                "backend": "pollinations-keyframes+ffmpeg",
                "prompt": prompt,
                "path": str(video_path),
                "seconds": seconds,
                "fps": fps,
                "keyframes": keyframes,
            }

    # No ffmpeg — export as GIF fallback
    all_frames = sorted(frames_dir.glob("frame_*.png"))
    pil_frames = [Image.open(f).convert("P", palette=Image.Palette.ADAPTIVE) for f in all_frames]
    gif_path = out_dir / f"{stamp()}_{slug(prompt)}.gif"
    pil_frames[0].save(
        gif_path, save_all=True, append_images=pil_frames[1:],
        duration=int(1000 / fps), loop=0,
    )

    import shutil as shutil_mod
    shutil_mod.rmtree(frames_dir, ignore_errors=True)

    if open_file:
        try:
            subprocess.Popen(["open", str(gif_path)])
        except Exception:
            pass

    return {
        "result": "video created (GIF — ffmpeg not available)",
        "backend": "pollinations-keyframes+gif",
        "prompt": prompt,
        "path": str(gif_path),
        "seconds": seconds,
        "fps": fps,
        "keyframes": keyframes,
    }


# ---------------------------------------------------------------------------
# List / status functions
# ---------------------------------------------------------------------------

def list_images(limit=40):
    all_files = []
    for folder, subfolder in [(IMAGE_OUT, "images"), (NSFW_OUT, "porn")]:
        if folder.exists():
            for p in sorted(folder.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True):
                if p.is_file():
                    all_files.append((p, subfolder))
    all_files.sort(key=lambda x: x[0].stat().st_mtime, reverse=True)
    all_files = all_files[:limit]
    return {
        "folder": str(IMAGE_OUT),
        "files": [
            {
                "name": p.name,
                "path": str(p),
                "download": f"{subfolder}/{p.name}",
                "size": p.stat().st_size,
            }
            for p, subfolder in all_files
        ],
    }


def list_videos(limit=40):
    folders = [VIDEO_OUT, NSFW_OUT]
    files = []
    for folder in folders:
        if folder.exists():
            for ext in ["*.mp4", "*.gif", "*.webm"]:
                files.extend(sorted(folder.glob(ext), key=lambda p: p.stat().st_mtime, reverse=True))
    files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    return {
        "folder": str(VIDEO_OUT),
        "files": [
            {"name": p.name, "path": str(p), "size": p.stat().st_size}
            for p in files
        ],
    }


def set_image_backend(backend):
    backend = str(backend or "").strip().lower()
    if backend not in ["pollinations", "comfyui", "local"]:
        return {"error": "Use pollinations, comfyui, or local."}
    cfg = load_config()
    cfg["image_backend"] = backend
    save_config(cfg)
    return {"result": "image backend updated", "image_backend": backend}


def set_image_enhance(value):
    value = str(value or "").strip().lower()
    enabled = value in ["1", "true", "yes", "on", "enhance"]
    cfg = load_config()
    cfg["image_enhance_prompt"] = enabled
    save_config(cfg)
    return {"result": "image prompt enhancement updated", "image_enhance_prompt": enabled}


def video_status():
    cfg = load_config()
    return {
        "video_backend": cfg.get("video_image_backend", "pollinations"),
        "video_width": cfg.get("video_width", 1024),
        "video_height": cfg.get("video_height", 576),
        "video_seconds": cfg.get("video_seconds", 8),
        "video_fps": cfg.get("video_fps", 24),
        "video_motion": cfg.get("video_motion", "high"),
        "video_keyframes": cfg.get("video_keyframes", 4),
        "video_quality": cfg.get("video_quality", "medium"),
        "nsfw_enabled": nsfw_enabled(),
    }


def set_video_quality(quality):
    quality = str(quality or "").strip().lower()
    presets = {
        "low": {"video_width": 640, "video_height": 360, "video_fps": 16, "video_keyframes": 2},
        "medium": {"video_width": 1024, "video_height": 576, "video_fps": 24, "video_keyframes": 4},
        "high": {"video_width": 1280, "video_height": 720, "video_fps": 30, "video_keyframes": 6},
    }
    if quality not in presets:
        return {"error": f"Use one of: {', '.join(presets.keys())}"}
    cfg = load_config()
    cfg.update(presets[quality])
    cfg["video_quality"] = quality
    save_config(cfg)
    return {"result": "video quality updated", **presets[quality]}


def set_video_motion(motion):
    motion = str(motion or "").strip().lower()
    if motion not in ["low", "medium", "high"]:
        return {"error": "Use low, medium, or high."}
    cfg = load_config()
    cfg["video_motion"] = motion
    save_config(cfg)
    return {"result": "video motion updated", "video_motion": motion}


def set_video_image_backend(backend):
    backend = str(backend or "").strip().lower()
    if backend not in ["pollinations", "local"]:
        return {"error": "Use pollinations or local."}
    cfg = load_config()
    cfg["video_image_backend"] = backend
    save_config(cfg)
    return {"result": "video image backend updated", "video_image_backend": backend}