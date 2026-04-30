from pathlib import Path
import re

base = Path("/Volumes/AI_DRIVE/TitanAgent")
assets = base / "assets"
assets.mkdir(exist_ok=True)

# -------------------------------------------------------------------
# 1) Write favicon / launch icon SVG
# -------------------------------------------------------------------
svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">
  <defs>
    <linearGradient id="yg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fff3a1"/>
      <stop offset="100%" stop-color="#e8dc67"/>
    </linearGradient>
    <linearGradient id="og" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffd08e"/>
      <stop offset="100%" stop-color="#e8ab43"/>
    </linearGradient>
    <linearGradient id="rg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#f8b0a7"/>
      <stop offset="100%" stop-color="#dd867b"/>
    </linearGradient>
  </defs>

  <rect x="10" y="40" width="26" height="34" rx="9" fill="url(#yg)"/>
  <rect x="32" y="16" width="28" height="58" rx="10" fill="url(#og)"/>
  <rect x="56" y="34" width="26" height="40" rx="9" fill="url(#rg)"/>

  <ellipse cx="43" cy="49" rx="5.8" ry="9.2" fill="#091335"/>
  <ellipse cx="57" cy="49" rx="5.8" ry="9.2" fill="#091335"/>

  <circle cx="44.3" cy="45.7" r="1.4" fill="white"/>
  <circle cx="58.3" cy="45.7" r="1.4" fill="white"/>
</svg>
"""

(assets / "titan_favicon.svg").write_text(svg, encoding="utf-8")
(assets / "titan_launch_icon.svg").write_text(svg, encoding="utf-8")

# -------------------------------------------------------------------
# 2) Patch control_panel.py
# -------------------------------------------------------------------
path = base / "control_panel.py"
text = path.read_text(encoding="utf-8")

backup = base / "backups" / "control_panel_before_preview_titan.py"
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

# Ensure asset serving import
if "send_from_directory" not in text:
    text = text.replace(
        "from flask import Flask, jsonify, render_template_string, request",
        "from flask import Flask, jsonify, render_template_string, request, send_from_directory"
    )

# Ensure favicon link
if 'href="/assets/titan_favicon.svg"' not in text and "<title>Titan</title>" in text:
    text = text.replace(
        "<title>Titan</title>",
        '<title>Titan</title>\n  <link rel="icon" href="/assets/titan_favicon.svg">'
    )

# Replace brand block
brand_replacement = '''
      <div class="brand">
        <div class="titan-mascot titan-mascot-sm titan-face" data-eye-scale="0.9" aria-hidden="true">
          <div class="seg seg-y"></div>
          <div class="seg seg-o"></div>
          <div class="seg seg-r"></div>

          <div class="eye-wrap eye-left"><div class="eye-core"></div></div>
          <div class="eye-wrap eye-right"><div class="eye-core"></div></div>
        </div>
        <span>Titan</span>
      </div>
'''

text = re.sub(
    r'<div class="brand">.*?</div>\s*\n\s*<nav>',
    brand_replacement + "\n      <nav>",
    text,
    count=1,
    flags=re.S
)

# Replace hero mascot section
hero_replacement = '''
          <div class="mascot-wrap">
            <div class="mascot-glow"></div>
            <div class="titan-mascot titan-mascot-lg titan-face floating" id="titanMascot" data-eye-scale="1.35">
              <div class="seg seg-y"></div>
              <div class="seg seg-o"></div>
              <div class="seg seg-r"></div>

              <div class="eye-wrap eye-left"><div class="eye-core"></div></div>
              <div class="eye-wrap eye-right"><div class="eye-core"></div></div>
            </div>
          </div>
'''

text = re.sub(
    r'<div class="mascot-wrap">.*?</div>\s*<div>',
    hero_replacement + "\n          <div>",
    text,
    count=1,
    flags=re.S
)

# Remove previous mascot CSS block if present
text = re.sub(
    r'/\* TITAN_PREVIEW_MASCOT_START \*/.*?/\* TITAN_PREVIEW_MASCOT_END \*/',
    '',
    text,
    flags=re.S
)

css = r'''
    /* TITAN_PREVIEW_MASCOT_START */
    .titan-mascot {
      position: relative;
      display: inline-block;
      user-select: none;
      filter: drop-shadow(0 10px 20px rgba(0,0,0,.28));
    }

    .titan-mascot .seg {
      position: absolute;
      bottom: 0;
      box-shadow:
        inset 0 6px 10px rgba(255,255,255,.18),
        inset 0 -10px 12px rgba(0,0,0,.10),
        0 2px 8px rgba(0,0,0,.08);
    }

    .titan-mascot .seg-y {
      background: linear-gradient(180deg, #fff3a1 0%, #f4df6d 35%, #e8dc67 100%);
    }

    .titan-mascot .seg-o {
      background: linear-gradient(180deg, #ffd08e 0%, #ffb85d 36%, #e8ab43 100%);
      z-index: 2;
    }

    .titan-mascot .seg-r {
      background: linear-gradient(180deg, #f8b0a7 0%, #f4968d 40%, #dd867b 100%);
      z-index: 1;
    }

    .titan-mascot-lg {
      width: 92px;
      height: 96px;
    }

    .titan-mascot-lg .seg-y {
      left: 6px;
      width: 28px;
      height: 42px;
      border-radius: 10px;
    }

    .titan-mascot-lg .seg-o {
      left: 28px;
      width: 30px;
      height: 76px;
      border-radius: 11px;
    }

    .titan-mascot-lg .seg-r {
      left: 56px;
      width: 28px;
      height: 50px;
      border-radius: 10px;
    }

    .titan-mascot-sm {
      width: 40px;
      height: 42px;
      margin-right: 10px;
      vertical-align: middle;
      filter: drop-shadow(0 6px 12px rgba(0,0,0,.22));
    }

    .titan-mascot-sm .seg-y {
      left: 2px;
      width: 12px;
      height: 18px;
      border-radius: 5px;
    }

    .titan-mascot-sm .seg-o {
      left: 11px;
      width: 14px;
      height: 33px;
      border-radius: 6px;
    }

    .titan-mascot-sm .seg-r {
      left: 22px;
      width: 12px;
      height: 25px;
      border-radius: 5px;
    }

    .titan-face .eye-wrap {
      position: absolute;
      overflow: hidden;
      border-radius: 999px;
      transform-origin: center center;
      background: transparent;
      z-index: 5;
      transition: transform .12s ease;
    }

    .titan-mascot-lg .eye-wrap {
      width: 14px;
      height: 22px;
      top: 35px;
    }

    .titan-mascot-lg .eye-left { left: 31px; }
    .titan-mascot-lg .eye-right { left: 47px; }

    .titan-mascot-sm .eye-wrap {
      width: 5px;
      height: 9px;
      top: 17px;
    }

    .titan-mascot-sm .eye-left { left: 15px; }
    .titan-mascot-sm .eye-right { left: 23px; }

    .titan-face .eye-core {
      position: absolute;
      inset: 0;
      border-radius: 999px;
      background: radial-gradient(circle at 35% 28%, #142755 0%, #091335 58%, #040a1f 100%);
      box-shadow:
        inset -1px -2px 3px rgba(0,0,0,.25),
        0 1px 2px rgba(0,0,0,.18);
      transform: translate(0px, 0px);
      transition: transform .08s linear;
    }

    .titan-face .eye-core::after {
      content: "";
      position: absolute;
      width: 28%;
      height: 28%;
      left: 28%;
      top: 16%;
      border-radius: 50%;
      background: rgba(255,255,255,.97);
    }

    .titan-face.blink .eye-wrap {
      transform: scaleY(0.08);
    }

    .floating {
      animation: titanFloat 3.2s ease-in-out infinite;
    }

    @keyframes titanFloat {
      0%   { transform: translateY(0px); }
      50%  { transform: translateY(-6px); }
      100% { transform: translateY(0px); }
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 22px;
      font-weight: 850;
      letter-spacing: -.04em;
    }

    .mascot-wrap {
      height: 150px;
      display: grid;
      place-items: center;
      position: relative;
    }

    .mascot-glow {
      position: absolute;
      width: 96px;
      height: 26px;
      bottom: 24px;
      border-radius: 50%;
      background: rgba(232,171,67,.22);
      filter: blur(16px);
    }

    .mini, .sprite, .px, .bar {
      display: none !important;
    }
    /* TITAN_PREVIEW_MASCOT_END */
'''

if "</style>" in text:
    text = text.replace("</style>", css + "\n  </style>", 1)

# Remove previous mascot JS block if present
text = re.sub(
    r'// TITAN_PREVIEW_MASCOT_JS_START.*?// TITAN_PREVIEW_MASCOT_JS_END',
    '',
    text,
    flags=re.S
)

js = r'''
// TITAN_PREVIEW_MASCOT_JS_START
window.addEventListener("DOMContentLoaded", () => {
  const faces = Array.from(document.querySelectorAll(".titan-face"));

  function blinkAll() {
    faces.forEach(face => face.classList.add("blink"));
    setTimeout(() => {
      faces.forEach(face => face.classList.remove("blink"));
    }, 130);
  }

  setInterval(blinkAll, 30000);

  window.addEventListener("mousemove", (e) => {
    faces.forEach(face => {
      const rect = face.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;

      let dx = (e.clientX - cx) / rect.width;
      let dy = (e.clientY - cy) / rect.height;

      dx = Math.max(-1, Math.min(1, dx));
      dy = Math.max(-1, Math.min(1, dy));

      const scale = parseFloat(face.dataset.eyeScale || "1");
      const mx = dx * 2.0 * scale;
      const my = dy * 1.2 * scale;

      face.querySelectorAll(".eye-core").forEach(eye => {
        eye.style.transform = `translate(${mx}px, ${my}px)`;
      });
    });
  });
});
// TITAN_PREVIEW_MASCOT_JS_END
'''

if "</script>" in text:
    text = text.replace("</script>", js + "\n</script>", 1)

# Add assets route if missing
if '@app.route("/assets/<path:name>")' not in text:
    route = '''
@app.route("/assets/<path:name>")
def titan_assets(name):
    return send_from_directory(str(BASE / "assets"), name)

'''
    text = text.replace('\n\nif __name__ == "__main__":', "\n\n" + route + '\nif __name__ == "__main__":')

path.write_text(text, encoding="utf-8")
print("Applied preview Titan mascot patch.")
print("Assets written:")
print(" -", assets / "titan_favicon.svg")
print(" -", assets / "titan_launch_icon.svg")
