from pathlib import Path
import re

base = Path("/Volumes/AI_DRIVE/TitanAgent")
assets = base / "assets"
assets.mkdir(exist_ok=True)

favicon_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">
  <defs>
    <linearGradient id="y" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fff17a"/>
      <stop offset="100%" stop-color="#e7dc67"/>
    </linearGradient>
    <linearGradient id="o" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffd083"/>
      <stop offset="100%" stop-color="#e8ab43"/>
    </linearGradient>
    <linearGradient id="r" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#f5a39e"/>
      <stop offset="100%" stop-color="#dd867b"/>
    </linearGradient>
  </defs>
  <rect x="14" y="36" width="22" height="34" rx="8" fill="url(#y)"/>
  <rect x="34" y="16" width="24" height="54" rx="9" fill="url(#o)"/>
  <rect x="56" y="30" width="22" height="40" rx="8" fill="url(#r)"/>
  <ellipse cx="45" cy="48" rx="5.2" ry="8.8" fill="#101735"/>
  <ellipse cx="61" cy="48" rx="5.2" ry="8.8" fill="#101735"/>
  <circle cx="46.3" cy="45.3" r="1.4" fill="white"/>
  <circle cx="62.3" cy="45.3" r="1.4" fill="white"/>
</svg>
"""

(assets / "titan_favicon.svg").write_text(favicon_svg)
(assets / "titan_launch_icon.svg").write_text(favicon_svg)

path = base / "control_panel.py"
text = path.read_text()

backup = base / "backups" / "control_panel_before_titan_mascot_final.py"
backup.parent.mkdir(exist_ok=True)
backup.write_text(text)

# import send_from_directory
text = text.replace(
    "from flask import Flask, jsonify, render_template_string, request",
    "from flask import Flask, jsonify, render_template_string, request, send_from_directory"
)

# favicon link
if '<link rel="icon" href="/assets/titan_favicon.svg">' not in text:
    text = text.replace(
        '<title>Titan</title>',
        '<title>Titan</title>\\n  <link rel="icon" href="/assets/titan_favicon.svg">'
    )

# replace sidebar brand block
brand_pattern = r'<div class="brand">.*?</div>\s*</div>\s*\n\s*<nav>'
brand_replacement = '''<div class="brand">
        <div class="titan-mascot titan-mascot-sm titan-face" data-eye-scale="1">
          <div class="seg seg-y"></div>
          <div class="seg seg-o"></div>
          <div class="seg seg-r"></div>

          <div class="eye-wrap eye-left"><div class="eye-core"></div></div>
          <div class="eye-wrap eye-right"><div class="eye-core"></div></div>
        </div>
        Titan
      </div>

      <nav>'''
text = re.sub(brand_pattern, brand_replacement, text, flags=re.S)

# replace hero mascot block
hero_pattern = r'<div class="mascot-wrap">.*?</div>\s*</section>'
hero_replacement = '''<div class="mascot-wrap">
            <div class="mascot-glow"></div>
            <div class="titan-mascot titan-mascot-lg titan-face floating" id="titanMascot" data-eye-scale="1.6">
              <div class="seg seg-y"></div>
              <div class="seg seg-o"></div>
              <div class="seg seg-r"></div>

              <div class="eye-wrap eye-left"><div class="eye-core"></div></div>
              <div class="eye-wrap eye-right"><div class="eye-core"></div></div>
            </div>
          </div>
        </section>'''
text = re.sub(hero_pattern, hero_replacement, text, flags=re.S)

css_block = r'''
    /* TITAN_MASCOT_FINAL */
    .titan-mascot {
      position: relative;
      display: inline-block;
      filter: drop-shadow(0 12px 24px rgba(0,0,0,.28));
      user-select: none;
    }

    .titan-mascot .seg {
      position: absolute;
      bottom: 0;
      box-shadow:
        inset 0 5px 8px rgba(255,255,255,.20),
        inset 0 -8px 10px rgba(0,0,0,.10);
    }

    .titan-mascot .seg-y {
      background: linear-gradient(180deg, #fff17a 0%, #e7dc67 100%);
    }

    .titan-mascot .seg-o {
      background: linear-gradient(180deg, #ffd083 0%, #e8ab43 100%);
    }

    .titan-mascot .seg-r {
      background: linear-gradient(180deg, #f5a39e 0%, #dd867b 100%);
    }

    .titan-mascot-lg {
      width: 92px;
      height: 96px;
    }

    .titan-mascot-lg .seg-y {
      left: 6px;
      width: 26px;
      height: 44px;
      border-radius: 9px;
    }

    .titan-mascot-lg .seg-o {
      left: 28px;
      width: 30px;
      height: 68px;
      border-radius: 10px;
      z-index: 2;
    }

    .titan-mascot-lg .seg-r {
      left: 52px;
      width: 26px;
      height: 50px;
      border-radius: 9px;
      z-index: 1;
    }

    .titan-mascot-sm {
      width: 42px;
      height: 44px;
      margin-right: 10px;
      vertical-align: middle;
    }

    .titan-mascot-sm .seg-y {
      left: 2px;
      width: 12px;
      height: 22px;
      border-radius: 5px;
    }

    .titan-mascot-sm .seg-o {
      left: 11px;
      width: 14px;
      height: 34px;
      border-radius: 6px;
      z-index: 2;
    }

    .titan-mascot-sm .seg-r {
      left: 22px;
      width: 12px;
      height: 26px;
      border-radius: 5px;
      z-index: 1;
    }

    .titan-face .eye-wrap {
      position: absolute;
      overflow: hidden;
      border-radius: 999px;
      transform-origin: center center;
      transition: transform .12s ease;
      z-index: 5;
      background: transparent;
    }

    .titan-mascot-lg .eye-wrap {
      width: 11px;
      height: 18px;
      top: 34px;
    }

    .titan-mascot-lg .eye-left { left: 34px; }
    .titan-mascot-lg .eye-right { left: 49px; }

    .titan-mascot-sm .eye-wrap {
      width: 5px;
      height: 9px;
      top: 18px;
    }

    .titan-mascot-sm .eye-left { left: 16px; }
    .titan-mascot-sm .eye-right { left: 24px; }

    .titan-face .eye-core {
      position: absolute;
      inset: 0;
      border-radius: 999px;
      background: #101735;
      box-shadow: inset -1px -2px 2px rgba(0,0,0,.20);
      transform: translate(0px, 0px);
      transition: transform .08s linear;
    }

    .titan-face .eye-core::after {
      content: "";
      position: absolute;
      width: 26%;
      height: 26%;
      left: 30%;
      top: 17%;
      border-radius: 50%;
      background: rgba(255,255,255,.96);
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
      width: 100px;
      height: 30px;
      bottom: 24px;
      border-radius: 50%;
      background: rgba(232,171,67,.20);
      filter: blur(16px);
    }

    .mini,
    .sprite,
    .px,
    .bar {
      display: none !important;
    }
'''

if "TITAN_MASCOT_FINAL" not in text:
    text = text.replace("</style>", css_block + "\n  </style>")

js_block = r'''
window.addEventListener("DOMContentLoaded", () => {
  const faces = Array.from(document.querySelectorAll(".titan-face"));

  function blinkAll() {
    faces.forEach(face => face.classList.add("blink"));
    setTimeout(() => faces.forEach(face => face.classList.remove("blink")), 130);
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
      const moveX = dx * 1.8 * scale;
      const moveY = dy * 1.2 * scale;

      face.querySelectorAll(".eye-core").forEach(eye => {
        eye.style.transform = `translate(${moveX}px, ${moveY}px)`;
      });
    });
  });
});
'''

if js_block not in text:
    text = text.replace("</script>", js_block + "\n</script>")

# assets route
if '@app.route("/assets/<path:name>")' not in text:
    insert_before = '\n\nif __name__ == "__main__":'
    route_code = '''
@app.route("/assets/<path:name>")
def titan_assets(name):
    return send_from_directory(str(BASE / "assets"), name)

'''
    text = text.replace(insert_before, "\n\n" + route_code + insert_before)

path.write_text(text)
print("Titan mascot patch installed.")
print("Wrote:")
print("-", assets / "titan_favicon.svg")
print("-", assets / "titan_launch_icon.svg")
