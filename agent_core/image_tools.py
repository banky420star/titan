from pathlib import Path
from datetime import datetime
from urllib.parse import quote
import json
import math
import random
import re
import ssl
import subprocess
import urllib.request

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
OUT = BASE / "downloads" / "images"
CONFIG = BASE / "config.json"
OUT.mkdir(parents=True, exist_ok=True)


def load_config():
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


def save_config(cfg):
    CONFIG.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def slug(text):
    text = str(text or "image").lower().strip()
    text = re.sub(r"[^a-z0-9._-]+", "-", text)
    return text.strip("-")[:70] or "image"


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


def clean_prompt(prompt):
    prompt = str(prompt or "").strip()
    prompt = re.sub(r"\s+", " ", prompt)
    return prompt[:1200]


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


def pollinations_url(prompt, width, height, seed=None):
    seed = seed if seed is not None else abs(hash(prompt)) % 99999999
    encoded = quote(enhance_prompt(prompt))
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={int(width)}&height={int(height)}"
        f"&seed={seed}"
        f"&nologo=true"
        f"&enhance=true"
        f"&model=flux"
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


def palette(prompt):
    seed = sum(ord(c) for c in str(prompt))
    random.seed(seed)
    return random.choice([
        ((17,18,20), (232,171,67), (221,134,123), (255,243,161)),
        ((9,15,30), (88,166,255), (190,130,255), (255,215,110)),
        ((18,14,24), (255,118,117), (253,203,110), (85,239,196)),
        ((10,22,20), (46,204,113), (241,196,15), (230,126,34)),
    ])


def draw_titan(draw, x, y, s=1.0, blink=False):
    def rr(a, b, c, d, r, fill):
        draw.rounded_rectangle([x+a*s, y+b*s, x+c*s, y+d*s], radius=r*s, fill=fill)

    rr(0, 42, 28, 86, 10, (246, 224, 100))
    rr(24, 8, 58, 86, 13, (232, 171, 67))
    rr(54, 32, 84, 86, 11, (221, 134, 123))

    eye = (5, 12, 38)

    if blink:
        draw.rounded_rectangle([x+35*s, y+54*s, x+49*s, y+58*s], radius=2*s, fill=eye)
        draw.rounded_rectangle([x+53*s, y+54*s, x+67*s, y+58*s], radius=2*s, fill=eye)
    else:
        draw.ellipse([x+35*s, y+43*s, x+49*s, y+66*s], fill=eye)
        draw.ellipse([x+53*s, y+43*s, x+67*s, y+66*s], fill=eye)
        draw.ellipse([x+40*s, y+47*s, x+44*s, y+51*s], fill=(255,255,255))
        draw.ellipse([x+58*s, y+47*s, x+62*s, y+51*s], fill=(255,255,255))


def local_fallback_image(prompt, width=1024, height=1024):
    bg, c1, c2, c3 = palette(prompt)
    random.seed(sum(ord(c) for c in prompt))

    img = Image.new("RGB", (width, height), bg).convert("RGBA")
    layer = Image.new("RGBA", (width, height), (0,0,0,0))
    d = ImageDraw.Draw(layer)

    for _ in range(22):
        x = random.randint(-150, width + 150)
        y = random.randint(-150, height + 150)
        r = random.randint(70, 260)
        col = random.choice([c1, c2, c3]) + (random.randint(34, 92),)
        d.ellipse([x-r, y-r, x+r, y+r], fill=col)

    layer = layer.filter(ImageFilter.GaussianBlur(26))
    img = Image.alpha_composite(img, layer)
    d = ImageDraw.Draw(img)

    d.rounded_rectangle(
        [80, height - 360, width - 80, height - 80],
        radius=34,
        fill=(255,255,255,30),
        outline=(255,255,255,55),
        width=2,
    )

    draw_titan(d, 120, height - 285, 1.45)
    d.text((250, height - 296), "Titan local fallback", font=font(48), fill=(255,255,255,245))

    y = height - 220
    words = clean_prompt(prompt).split()
    lines = []
    line = []

    for word in words:
        if len(" ".join(line + [word])) > 36:
            lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)

    if line:
        lines.append(" ".join(line))

    for line in lines[:6]:
        d.text((250, y), line, font=font(28), fill=(222,222,230,235))
        y += 40

    return img.convert("RGB")


def create_image(prompt, width=None, height=None, open_file=True):
    cfg = load_config()
    backend = cfg.get("image_backend", "pollinations")
    prompt = clean_prompt(prompt)

    width = int(width or cfg.get("image_width", 768))
    height = int(height or cfg.get("image_height", 768))

    if backend == "comfyui":
        from agent_core.comfyui_bridge import comfy_image
        return comfy_image(
            prompt,
            width=width,
            height=height,
            steps=int(cfg.get("comfy_steps", 4)),
            cfg=float(cfg.get("comfy_cfg", 1.0)),
        )

    path = OUT / f"{stamp()}_{slug(prompt)}.png"

    if backend == "pollinations":
        try:
            url = pollinations_url(prompt, width, height)
            download_image(url, path)
            used_backend = "pollinations-flux"
        except Exception as e:
            img = local_fallback_image(prompt, width, height)
            path = OUT / f"{stamp()}_{slug(prompt)}_fallback.png"
            img.save(path)
            used_backend = "local fallback after pollinations error: " + repr(e)
    else:
        img = local_fallback_image(prompt, width, height)
        img.save(path)
        used_backend = "local fallback"

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


def create_gif(prompt, width=None, height=None, frames=28, open_file=True):
    cfg = load_config()
    width = int(width or cfg.get("gif_width", 768))
    height = int(height or cfg.get("gif_height", 512))
    prompt = clean_prompt(prompt)

    base_result = create_image(prompt, width=width, height=height, open_file=False)
    base = Image.open(base_result["path"]).convert("RGB")
    base = base.resize((width, height))

    imgs = []

    for i in range(frames):
        t = i / frames
        zoom = 1.0 + 0.035 * math.sin(t * math.tau)
        dx = int(12 * math.sin(t * math.tau))
        dy = int(8 * math.cos(t * math.tau))

        crop_w = int(width / zoom)
        crop_h = int(height / zoom)
        left = max(0, min(width - crop_w, (width - crop_w)//2 + dx))
        top = max(0, min(height - crop_h, (height - crop_h)//2 + dy))

        frame = base.crop((left, top, left + crop_w, top + crop_h)).resize((width, height))
        overlay = Image.new("RGBA", (width, height), (0,0,0,0))
        d = ImageDraw.Draw(overlay)

        draw_titan(d, width - 120, height - 138, 1.0, blink=i in [8, 9, 20])

        frame = Image.alpha_composite(frame.convert("RGBA"), overlay).convert("P", palette=Image.Palette.ADAPTIVE)
        imgs.append(frame)

    path = OUT / f"{stamp()}_{slug(prompt)}.gif"
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=80, loop=0)

    if open_file:
        try:
            subprocess.Popen(["open", str(path)])
        except Exception:
            pass

    return {
        "result": "gif created",
        "backend": "animated generated image",
        "source_image": base_result["path"],
        "path": str(path),
        "frames": frames,
    }


def list_images(limit=40):
    files = sorted(OUT.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    return {
        "folder": str(OUT),
        "files": [
            {"name": p.name, "path": str(p), "size": p.stat().st_size}
            for p in files
            if p.is_file()
        ],
    }


def set_image_backend(backend):
    backend = str(backend or "").strip().lower()
    if backend not in ["pollinations", "local"]:
        return {"error": "Use pollinations or local."}

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
