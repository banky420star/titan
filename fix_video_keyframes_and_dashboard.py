from pathlib import Path
import json
import re

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
BACKUPS = BASE / "backups"
BACKUPS.mkdir(exist_ok=True)

video_tools = BASE / "agent_core" / "video_tools.py"
terminal = BASE / "titan_terminal.py"
dashboard = BASE / "control_panel.py"
natural = BASE / "agent_core" / "natural_media.py"

for p in [video_tools, terminal, dashboard, natural]:
    if p.exists():
        (BACKUPS / (p.name + ".before_video_keyframe_fix")).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

video_tools.write_text(r'''
from pathlib import Path
from datetime import datetime
import json
import math
import re
import subprocess

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
CONFIG = BASE / "config.json"
VIDEO_OUT = BASE / "downloads" / "videos"
IMAGE_OUT = BASE / "downloads" / "images"

VIDEO_OUT.mkdir(parents=True, exist_ok=True)
IMAGE_OUT.mkdir(parents=True, exist_ok=True)


def load_config():
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


def save_config(cfg):
    CONFIG.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def slug(text):
    text = str(text or "video").strip().lower()
    text = re.sub(r"[^a-z0-9._-]+", "-", text)
    return text.strip("-")[:80] or "video"


def clean_prompt(prompt):
    prompt = str(prompt or "").strip()
    prompt = re.sub(r"\s+", " ", prompt)
    return prompt[:1200]


def font(size):
    for path in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/System/Library/Fonts/Supplemental/Verdana.ttf",
        "/System/Library/Fonts/Menlo.ttc",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def scene_type(prompt):
    p = prompt.lower()
    if any(x in p for x in ["trading", "dashboard", "chart", "terminal", "code", "coding", "software"]):
        return "dashboard"
    if any(x in p for x in ["car", "ferrari", "driving", "race", "road", "vehicle"]):
        return "car"
    if any(x in p for x in ["beach", "ocean", "waves", "sunset", "surf"]):
        return "beach"
    if any(x in p for x in ["mascot", "titan", "robot", "character"]):
        return "mascot"
    return "cinematic"


def video_settings():
    cfg = load_config()
    quality = str(cfg.get("video_quality", "medium")).lower()
    motion = str(cfg.get("video_motion", "high")).lower()
    presets = {
        "low": {"width": 640, "height": 360, "seconds": 5, "fps": 12, "keyframes": 3},
        "medium": {"width": 1024, "height": 576, "seconds": 7, "fps": 18, "keyframes": 4},
        "high": {"width": 1280, "height": 720, "seconds": 8, "fps": 24, "keyframes": 5},
    }
    base = presets.get(quality, presets["medium"])
    return {
        "quality": quality,
        "motion": motion,
        "width": int(cfg.get("video_width", base["width"])),
        "height": int(cfg.get("video_height", base["height"])),
        "seconds": int(cfg.get("video_seconds", base["seconds"])),
        "fps": int(cfg.get("video_fps", base["fps"])),
        "keyframes": int(cfg.get("video_keyframes", base["keyframes"])),
        "video_image_backend": cfg.get("video_image_backend", "pollinations"),
    }


def keyframe_prompts(prompt, count):
    prompt = clean_prompt(prompt)
    scene = scene_type(prompt)
    quality = "cinematic video frame, coherent subject, high quality, sharp focus, professional lighting, no random objects, no text artifacts, no watermark"

    packs = {
        "dashboard": [
            "wide shot of a neon software dashboard with clear trading charts",
            "close shot of terminal code and animated-looking UI panels",
            "dynamic angle of glowing dashboard panels and graphs",
            "hero shot of cute Titan three-bar mascot working at the dashboard",
            "final polished product reveal with cinematic lighting",
        ],
        "car": [
            "wide cinematic road scene with the car clearly visible",
            "side tracking shot of the car in motion, realistic wheels and reflections",
            "low angle dynamic car shot with motion blur",
            "close hero shot of the car with sunset lighting",
            "final wide shot of road, environment, and car",
        ],
        "beach": [
            "wide beach scene with realistic ocean and sunset",
            "medium shot with wave motion feeling and clear subject placement",
            "cinematic beach atmosphere with wind and water movement",
            "golden hour shot with waves and sand",
            "final polished sunset beach frame",
        ],
        "mascot": [
            "wide shot showing the Titan three-bar mascot clearly",
            "mascot moving through a glowing terminal space",
            "mascot interacting with floating UI elements",
            "hero shot of cute mascot with large expressive eyes",
            "final polished mascot reveal",
        ],
        "cinematic": [
            "wide establishing shot",
            "medium shot with subject movement and depth",
            "dynamic close shot with cinematic lighting",
            "dramatic motion frame with clean composition",
            "final polished hero frame",
        ],
    }

    steps = packs.get(scene, packs["cinematic"])
    return [f"{prompt}, {steps[i % len(steps)]}, {quality}" for i in range(count)]


def fallback_frame(prompt, width, height, index=0):
    palettes = [
        ((14,16,22), (232,171,67), (221,134,123), (88,166,255)),
        ((8,12,28), (88,166,255), (190,130,255), (255,215,110)),
        ((18,14,24), (255,118,117), (253,203,110), (85,239,196)),
    ]
    bg, c1, c2, c3 = palettes[index % len(palettes)]
    img = Image.new("RGB", (width, height), bg).convert("RGBA")
    layer = Image.new("RGBA", (width, height), (0,0,0,0))
    d = ImageDraw.Draw(layer)

    for i in range(18):
        x = int(width * ((i * 0.37 + index * 0.13) % 1))
        y = int(height * ((i * 0.61 + index * 0.17) % 1))
        r = 90 + (i % 7) * 28
        col = [c1, c2, c3][i % 3] + (55,)
        d.ellipse([x-r, y-r, x+r, y+r], fill=col)

    layer = layer.filter(ImageFilter.GaussianBlur(28))
    img = Image.alpha_composite(img, layer)
    d = ImageDraw.Draw(img)

    d.rounded_rectangle([55, height-165, width-55, height-38], radius=28, fill=(0,0,0,120), outline=(255,255,255,45), width=2)
    d.text((82, height-142), "Titan keyframe video", font=font(34), fill=(255,255,255,240))

    short = clean_prompt(prompt)
    if len(short) > 90:
        short = short[:90] + "..."
    d.text((82, height-86), short, font=font(21), fill=(230,230,236,225))
    return img.convert("RGB")


def generate_keyframe(prompt, width, height, index):
    cfg = load_config()
    backend = cfg.get("video_image_backend", "pollinations")

    old_backend = cfg.get("image_backend")
    old_width = cfg.get("image_width")
    old_height = cfg.get("image_height")

    try:
        cfg["image_backend"] = backend
        cfg["image_width"] = width
        cfg["image_height"] = height
        save_config(cfg)

        from agent_core.image_tools import create_image
        result = create_image(prompt, width=width, height=height, open_file=False)
        path = result.get("path")

        if path and Path(path).exists():
            return Image.open(path).convert("RGB").resize((width, height)), path, result.get("backend")
    except Exception:
        pass
    finally:
        cfg = load_config()
        if old_backend is not None:
            cfg["image_backend"] = old_backend
        if old_width is not None:
            cfg["image_width"] = old_width
        if old_height is not None:
            cfg["image_height"] = old_height
        save_config(cfg)

    img = fallback_frame(prompt, width, height, index)
    path = IMAGE_OUT / f"{stamp()}_{slug(prompt)}_video_fallback_{index}.png"
    img.save(path)
    return img, str(path), "fallback-keyframe"


def ease(x):
    return x * x * (3 - 2 * x)


def camera_transform(img, width, height, t, direction, motion_strength):
    zoom = 1.0 + motion_strength * 0.075 * ease(t)
    crop_w = int(width / zoom)
    crop_h = int(height / zoom)
    max_x = max(0, width - crop_w)
    max_y = max(0, height - crop_h)

    if direction % 4 == 0:
        left = int(max_x * ease(t))
        top = int(max_y * 0.30)
    elif direction % 4 == 1:
        left = int(max_x * (1 - ease(t)))
        top = int(max_y * 0.70)
    elif direction % 4 == 2:
        left = int(max_x * 0.5)
        top = int(max_y * ease(t))
    else:
        left = int(max_x * 0.5 + math.sin(t * math.tau) * max_x * 0.35)
        top = int(max_y * 0.5 + math.cos(t * math.tau) * max_y * 0.25)

    left = max(0, min(max_x, left))
    top = max(0, min(max_y, top))
    return img.crop((left, top, left + crop_w, top + crop_h)).resize((width, height), Image.Resampling.LANCZOS)


def draw_motion_fx(frame, t, scene, prompt):
    width, height = frame.size
    overlay = Image.new("RGBA", (width, height), (0,0,0,0))
    d = ImageDraw.Draw(overlay)

    if scene in ["dashboard", "cinematic", "mascot"]:
        for i in range(16):
            x = int(width * ((i * 0.19 + t * 0.35) % 1))
            y = int(height * ((i * 0.31 + math.sin(t * math.tau + i) * 0.05) % 1))
            d.ellipse([x-3, y-3, x+3, y+3], fill=(232,171,67,95))

    if scene == "dashboard":
        scan_x = int(width * ((t * 1.35) % 1))
        d.rectangle([scan_x, 0, scan_x+8, height], fill=(88,166,255,45))
    elif scene == "car":
        for i in range(14):
            y = int(height * (0.18 + i * 0.05))
            x = int(width * ((1 - t * 1.8 + i * 0.11) % 1))
            d.line([x, y, x-130, y+12], fill=(255,255,255,65), width=3)
    elif scene == "beach":
        for i in range(5):
            y = int(height * (0.55 + i * 0.055 + math.sin(t * math.tau + i) * 0.006))
            d.arc([0, y-40, width, y+60], 0, 180, fill=(255,255,255,85), width=3)

    title = clean_prompt(prompt)
    if len(title) > 78:
        title = title[:78] + "..."
    d.rounded_rectangle([34, height-82, width-34, height-28], radius=18, fill=(0,0,0,95), outline=(255,255,255,30), width=1)
    d.text((56, height-66), title, font=font(18), fill=(245,245,250,225))
    return Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")


def create_video(prompt, width=None, height=None, seconds=None, fps=None, open_file=True):
    prompt = clean_prompt(prompt)
    settings = video_settings()

    width = int(width or settings["width"])
    height = int(height or settings["height"])
    seconds = int(seconds or settings["seconds"])
    fps = int(fps or settings["fps"])
    keyframe_count = max(3, int(settings["keyframes"]))

    motion_strength = {"low": 0.45, "medium": 0.75, "high": 1.0}.get(settings["motion"], 1.0)
    scene = scene_type(prompt)
    prompts = keyframe_prompts(prompt, keyframe_count)

    keyframes = []
    keyframe_files = []
    backends = []

    for idx, p in enumerate(prompts):
        img, path, backend = generate_keyframe(p, width, height, idx)
        keyframes.append(img)
        keyframe_files.append(path)
        backends.append(backend)

    total_frames = max(1, seconds * fps)
    segment_count = len(keyframes) - 1
    frames_per_segment = max(4, total_frames // segment_count)
    frames = []

    for idx in range(segment_count):
        a = keyframes[idx]
        b = keyframes[idx + 1]
        for i in range(frames_per_segment):
            t = i / max(1, frames_per_segment - 1)
            a_cam = camera_transform(a, width, height, t, idx, motion_strength)
            b_cam = camera_transform(b, width, height, t, idx + 1, motion_strength)
            alpha = 0.0 if t < 0.62 else ease((t - 0.62) / 0.38)
            frame = Image.blend(a_cam, b_cam, alpha)
            frame = draw_motion_fx(frame, t, scene, prompt)
            frames.append(np.array(frame))

    frames = frames[:total_frames]
    if len(frames) < total_frames and frames:
        frames.extend([frames[-1]] * (total_frames - len(frames)))

    path = VIDEO_OUT / f"{stamp()}_{slug(prompt)}.mp4"
    imageio.mimsave(path, frames, fps=fps, codec="libx264", quality=8, macro_block_size=1)

    if open_file:
        try:
            subprocess.Popen(["open", str(path)])
        except Exception:
            pass

    return {
        "result": "video created",
        "backend": "generated-keyframe-video-v3",
        "path": str(path),
        "prompt": prompt,
        "scene": scene,
        "width": width,
        "height": height,
        "seconds": seconds,
        "fps": fps,
        "quality": settings["quality"],
        "motion": settings["motion"],
        "video_image_backend": settings["video_image_backend"],
        "keyframes": keyframe_files,
        "keyframe_backends": backends,
    }


def list_videos(limit=40):
    files = sorted(VIDEO_OUT.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)[:int(limit)]
    return {"folder": str(VIDEO_OUT), "files": [{"name": p.name, "path": str(p), "size": p.stat().st_size} for p in files]}


def set_video_quality(quality):
    quality = str(quality or "").strip().lower()
    if quality not in ["low", "medium", "high"]:
        return {"error": "Use low, medium, or high."}
    presets = {
        "low": {"video_width": 640, "video_height": 360, "video_seconds": 5, "video_fps": 12, "video_keyframes": 3},
        "medium": {"video_width": 1024, "video_height": 576, "video_seconds": 7, "video_fps": 18, "video_keyframes": 4},
        "high": {"video_width": 1280, "video_height": 720, "video_seconds": 8, "video_fps": 24, "video_keyframes": 5},
    }
    cfg = load_config()
    cfg["video_quality"] = quality
    cfg.update(presets[quality])
    save_config(cfg)
    return {"result": "video quality updated", "video_quality": quality, **presets[quality]}


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
    if backend not in ["pollinations", "comfyui", "local"]:
        return {"error": "Use pollinations, comfyui, or local."}
    cfg = load_config()
    cfg["video_image_backend"] = backend
    save_config(cfg)
    return {"result": "video image backend updated", "video_image_backend": backend}


def video_status():
    return {
        "settings": video_settings(),
        "output": str(VIDEO_OUT),
        "note": "generated-keyframe-video-v3 creates multiple generated frames and transitions between them, instead of drawing fake stick figures or random 2D cars."
    }
''', encoding="utf-8")

# terminal commands
text = terminal.read_text(encoding="utf-8")

helpers = r'''
def terminal_create_video(args):
    try:
        import json
        from agent_core.video_tools import create_video
        prompt = str(args or "").strip()
        if not prompt:
            say_panel("Usage: /video <prompt>", title="Video", style="yellow")
            return
        result = create_video(prompt)
        say_panel(json.dumps(result, indent=2), title="Video Created", style="green")
    except Exception as e:
        say_panel("Video creation failed: " + repr(e), title="Video", style="red")


def terminal_list_videos():
    try:
        import json
        from agent_core.video_tools import list_videos
        say_panel(json.dumps(list_videos(), indent=2), title="Videos", style="cyan")
    except Exception as e:
        say_panel("Videos failed: " + repr(e), title="Videos", style="red")


def terminal_video_quality(args):
    try:
        import json
        from agent_core.video_tools import set_video_quality
        say_panel(json.dumps(set_video_quality(args), indent=2), title="Video Quality", style="green")
    except Exception as e:
        say_panel("Video quality failed: " + repr(e), title="Video Quality", style="red")


def terminal_video_motion(args):
    try:
        import json
        from agent_core.video_tools import set_video_motion
        say_panel(json.dumps(set_video_motion(args), indent=2), title="Video Motion", style="green")
    except Exception as e:
        say_panel("Video motion failed: " + repr(e), title="Video Motion", style="red")


def terminal_video_image_backend(args):
    try:
        import json
        from agent_core.video_tools import set_video_image_backend
        say_panel(json.dumps(set_video_image_backend(args), indent=2), title="Video Image Backend", style="green")
    except Exception as e:
        say_panel("Video image backend failed: " + repr(e), title="Video Image Backend", style="red")


def terminal_video_status():
    try:
        import json
        from agent_core.video_tools import video_status
        say_panel(json.dumps(video_status(), indent=2), title="Video Status", style="cyan")
    except Exception as e:
        say_panel("Video status failed: " + repr(e), title="Video Status", style="red")


'''

if "def terminal_create_video(" not in text:
    text = text.replace("def repl():", helpers + "\ndef repl():", 1)

intercept = r'''
            # TITAN_VIDEO_KEYFRAME_COMMANDS_V3
            if lower.startswith("/video "):
                terminal_create_video(command.replace("/video ", "", 1).strip())
                continue

            if lower == "/videos":
                terminal_list_videos()
                continue

            if lower == "/video-status":
                terminal_video_status()
                continue

            if lower.startswith("/video-quality "):
                terminal_video_quality(command.replace("/video-quality ", "", 1).strip())
                continue

            if lower.startswith("/video-motion "):
                terminal_video_motion(command.replace("/video-motion ", "", 1).strip())
                continue

            if lower.startswith("/video-image-backend "):
                terminal_video_image_backend(command.replace("/video-image-backend ", "", 1).strip())
                continue

'''

if "TITAN_VIDEO_KEYFRAME_COMMANDS_V3" not in text:
    repl_start = text.find("def repl():")
    after = text[repl_start:]
    match = re.search(r"\n\s*if\s+lower\b", after)
    if not match:
        raise SystemExit("Could not find terminal insertion point.")
    pos = repl_start + match.start()
    text = text[:pos] + intercept + text[pos:]

terminal.write_text(text, encoding="utf-8")

# natural media
if natural.exists():
    nt = natural.read_text(encoding="utf-8")
else:
    nt = "import json\n\n\ndef route_natural_media(command):\n    return None\n"

if "VIDEO_PREFIXES" not in nt:
    nt = nt.replace("IMAGE_PREFIXES = [", '''VIDEO_PREFIXES = [
    "create video",
    "create a video",
    "make video",
    "make a video",
    "generate video",
    "generate a video",
    "create mp4",
    "make mp4",
]


IMAGE_PREFIXES = [''')

if "video_prompt = strip_prefix(command, VIDEO_PREFIXES)" not in nt:
    nt = nt.replace("image_prompt = strip_prefix(command, IMAGE_PREFIXES)", '''video_prompt = strip_prefix(command, VIDEO_PREFIXES)
    if video_prompt is not None:
        if not video_prompt:
            return {"handled": True, "text": "Usage: create video <what should move>"}
        from agent_core.video_tools import create_video
        return {"handled": True, "text": json.dumps(create_video(video_prompt), indent=2)}

    image_prompt = strip_prefix(command, IMAGE_PREFIXES)''')

natural.write_text(nt, encoding="utf-8")

# dashboard routes
if dashboard.exists():
    dt = dashboard.read_text(encoding="utf-8")

    routes = r'''
@app.route("/api/video/create", methods=["POST"])
def api_video_create():
    from agent_core.video_tools import create_video
    return safe(lambda: create_video(request.json.get("prompt", "")))


@app.route("/api/video/list")
def api_video_list():
    from agent_core.video_tools import list_videos
    return safe(lambda: list_videos())


@app.route("/api/video/status")
def api_video_status():
    from agent_core.video_tools import video_status
    return safe(lambda: video_status())


@app.route("/api/video/quality", methods=["POST"])
def api_video_quality():
    from agent_core.video_tools import set_video_quality
    return safe(lambda: set_video_quality(request.json.get("quality", "medium")))


@app.route("/api/video/motion", methods=["POST"])
def api_video_motion():
    from agent_core.video_tools import set_video_motion
    return safe(lambda: set_video_motion(request.json.get("motion", "high")))


@app.route("/api/video/image-backend", methods=["POST"])
def api_video_image_backend():
    from agent_core.video_tools import set_video_image_backend
    return safe(lambda: set_video_image_backend(request.json.get("backend", "pollinations")))

'''

    if '@app.route("/api/video/create")' not in dt:
        dt = dt.replace('\n\nif __name__ == "__main__":', "\n\n" + routes + '\nif __name__ == "__main__":')

    if "showView('video'" not in dt:
        dt = dt.replace(
            '<button class="active" onclick="showView(\'chat\', this)">💬 Chat</button>',
            '<button class="active" onclick="showView(\'chat\', this)">💬 Chat</button>\n        <button onclick="showView(\'video\', this); loadVideos()">▣ Video</button>',
            1
        )

    if 'id="view-video"' not in dt:
        video_section = r'''
        <section id="view-video" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Video Studio</strong>
              <button class="btn" onclick="loadVideoStatus()">Status</button>
            </div>
            <div class="panel-body">
              <div class="row">
                <select class="field small-field" id="videoQuality"><option value="low">low</option><option value="medium" selected>medium</option><option value="high">high</option></select>
                <button class="btn" onclick="setVideoQuality()">Set Quality</button>
                <select class="field small-field" id="videoMotion"><option value="low">low</option><option value="medium">medium</option><option value="high" selected>high</option></select>
                <button class="btn" onclick="setVideoMotion()">Set Motion</button>
                <select class="field small-field" id="videoImageBackend"><option value="pollinations" selected>pollinations</option><option value="comfyui">comfyui</option><option value="local">local</option></select>
                <button class="btn" onclick="setVideoImageBackend()">Set Backend</button>
              </div>
              <textarea id="videoPrompt" class="file-editor" placeholder="Describe the video...">a cute Titan three-bar mascot building a neon trading dashboard, animated charts, typing code, glowing terminal</textarea>
              <div class="row">
                <button class="btn primary" onclick="createDashboardVideo()">Create Video</button>
                <button class="btn" onclick="loadVideos()">Refresh Videos</button>
              </div>
              <pre id="videoOut">Video output appears here.</pre>
              <div id="videoList" class="history-list">No videos loaded.</div>
            </div>
          </div>
        </section>
'''
        dt = dt.replace('<section id="view-chat" class="view active">', video_section + '\n\n<section id="view-chat" class="view active">', 1)

    js = r'''
// TITAN_VIDEO_DASHBOARD_V3
async function loadVideoStatus() {
  const out = document.getElementById("videoOut");
  const data = await jsonFetch("/api/video/status");
  if (out) out.textContent = JSON.stringify(data, null, 2);
}
async function setVideoQuality() {
  const q = document.getElementById("videoQuality").value;
  const data = await jsonFetch("/api/video/quality", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({quality:q})});
  document.getElementById("videoOut").textContent = JSON.stringify(data, null, 2);
}
async function setVideoMotion() {
  const m = document.getElementById("videoMotion").value;
  const data = await jsonFetch("/api/video/motion", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({motion:m})});
  document.getElementById("videoOut").textContent = JSON.stringify(data, null, 2);
}
async function setVideoImageBackend() {
  const backend = document.getElementById("videoImageBackend").value;
  const data = await jsonFetch("/api/video/image-backend", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({backend})});
  document.getElementById("videoOut").textContent = JSON.stringify(data, null, 2);
}
async function createDashboardVideo() {
  const prompt = document.getElementById("videoPrompt").value.trim();
  const out = document.getElementById("videoOut");
  out.textContent = "Creating generated keyframe video...";
  const data = await jsonFetch("/api/video/create", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({prompt})});
  out.textContent = JSON.stringify(data, null, 2);
  await loadVideos();
}
async function loadVideos() {
  const list = document.getElementById("videoList");
  if (!list) return;
  const data = await jsonFetch("/api/video/list");
  const files = data.files || [];
  if (!files.length) { list.textContent = "No videos found."; return; }
  list.innerHTML = "";
  files.forEach(file => {
    const div = document.createElement("div");
    div.className = "video-item";
    div.textContent = file.name + " | " + file.size + " bytes";
    div.onclick = () => { document.getElementById("videoOut").textContent = JSON.stringify(file, null, 2); };
    list.appendChild(div);
  });
}
'''
    if "TITAN_VIDEO_DASHBOARD_V3" not in dt:
        dt = dt.replace("</script>", js + "\n</script>", 1)

    css = r'''
/* TITAN_VIDEO_DASHBOARD_V3 */
.video-item { border: 1px solid var(--line); background: rgba(255,255,255,.045); border-radius: 14px; padding: 10px; margin: 8px; cursor: pointer; }
#videoOut { max-height: 500px; overflow-y: auto; margin: 14px; padding: 14px; border-radius: 16px; border: 1px solid var(--line); background: rgba(0,0,0,.18); }
'''
    if "TITAN_VIDEO_DASHBOARD_V3" not in dt.split("</style>")[0]:
        dt = dt.replace("</style>", css + "\n</style>", 1)

    dashboard.write_text(dt, encoding="utf-8")

# config defaults
cfg_path = BASE / "config.json"
cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
cfg.update({
    "video_quality": "medium",
    "video_motion": "high",
    "video_image_backend": "pollinations",
    "video_width": 1024,
    "video_height": 576,
    "video_seconds": 7,
    "video_fps": 18,
    "video_keyframes": 4,
})
cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

print("video keyframe + dashboard fix installed")
