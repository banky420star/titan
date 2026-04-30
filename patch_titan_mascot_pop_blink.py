from pathlib import Path
import re

path = Path("control_panel.py")
text = path.read_text(encoding="utf-8")

backup = Path("backups/control_panel_before_pop_blink.py")
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

new_css = r'''
    /* TITAN_PREVIEW_MASCOT_START */
    .titan-mascot {
      position: relative;
      display: inline-block;
      user-select: none;
      filter:
        drop-shadow(0 16px 28px rgba(0,0,0,.30))
        drop-shadow(0 0 18px rgba(232,171,67,.10));
      transform-style: preserve-3d;
    }

    .titan-mascot .seg {
      position: absolute;
      bottom: 0;
      box-shadow:
        inset 0 10px 14px rgba(255,255,255,.22),
        inset 0 -12px 16px rgba(0,0,0,.12),
        inset -4px 0 8px rgba(0,0,0,.06),
        0 8px 16px rgba(0,0,0,.12);
    }

    .titan-mascot .seg-y {
      background:
        radial-gradient(circle at 30% 20%, rgba(255,255,255,.33), transparent 42%),
        linear-gradient(180deg, #fff6a8 0%, #f9ea7d 38%, #e8dc67 100%);
    }

    .titan-mascot .seg-o {
      background:
        radial-gradient(circle at 30% 18%, rgba(255,255,255,.28), transparent 40%),
        linear-gradient(180deg, #ffd89d 0%, #ffc063 34%, #e8ab43 100%);
      z-index: 2;
    }

    .titan-mascot .seg-r {
      background:
        radial-gradient(circle at 30% 20%, rgba(255,255,255,.26), transparent 42%),
        linear-gradient(180deg, #f9b6ae 0%, #f39a91 36%, #dd867b 100%);
      z-index: 1;
    }

    .titan-mascot-lg {
      width: 128px;
      height: 106px;
    }

    .titan-mascot-lg .seg-y {
      left: 13px;
      bottom: 8px;
      width: 38px;
      height: 52px;
      border-radius: 15px;
    }

    .titan-mascot-lg .seg-o {
      left: 45px;
      bottom: 8px;
      width: 40px;
      height: 88px;
      border-radius: 16px;
    }

    .titan-mascot-lg .seg-r {
      left: 78px;
      bottom: 8px;
      width: 38px;
      height: 60px;
      border-radius: 15px;
    }

    .titan-mascot-sm {
      width: 42px;
      height: 42px;
      margin-right: 10px;
      vertical-align: middle;
      filter:
        drop-shadow(0 8px 14px rgba(0,0,0,.24))
        drop-shadow(0 0 12px rgba(232,171,67,.08));
    }

    .titan-mascot-sm .seg-y {
      left: 3px;
      bottom: 3px;
      width: 12px;
      height: 20px;
      border-radius: 5px;
    }

    .titan-mascot-sm .seg-o {
      left: 14px;
      bottom: 3px;
      width: 13px;
      height: 34px;
      border-radius: 6px;
      z-index: 2;
    }

    .titan-mascot-sm .seg-r {
      left: 25px;
      bottom: 3px;
      width: 12px;
      height: 24px;
      border-radius: 5px;
      z-index: 1;
    }

    .titan-face .eye-wrap {
      position: absolute;
      overflow: hidden;
      border-radius: 999px;
      transform-origin: center center;
      background: transparent;
      z-index: 5;
      transition: transform .14s ease;
    }

    /* Slightly smaller than before, still cute */
    .titan-mascot-lg .eye-wrap {
      width: 17px;
      height: 26px;
      top: 49px;
    }

    .titan-mascot-lg .eye-left {
      left: 48px;
    }

    .titan-mascot-lg .eye-right {
      left: 68px;
    }

    .titan-mascot-sm .eye-wrap {
      width: 6px;
      height: 10px;
      top: 18px;
    }

    .titan-mascot-sm .eye-left {
      left: 16px;
    }

    .titan-mascot-sm .eye-right {
      left: 24px;
    }

    .titan-face .eye-core {
      position: absolute;
      inset: 0;
      border-radius: 999px;
      background:
        radial-gradient(circle at 38% 28%, #243f82 0%, #13254f 34%, #091335 64%, #020611 100%);
      box-shadow:
        inset -2px -3px 5px rgba(0,0,0,.28),
        0 1px 2px rgba(0,0,0,.18);
      transform: translate(0px, 0px);
      transition: transform .09s linear;
    }

    .titan-face .eye-core::after {
      content: "";
      position: absolute;
      width: 30%;
      height: 30%;
      left: 24%;
      top: 14%;
      border-radius: 50%;
      background: rgba(255,255,255,.99);
      box-shadow: 0 0 4px rgba(255,255,255,.45);
    }

    .titan-face.blink .eye-wrap {
      transform: scaleY(0.05);
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
      width: 116px;
      height: 34px;
      bottom: 20px;
      border-radius: 50%;
      background:
        radial-gradient(circle, rgba(255,203,96,.26) 0%, rgba(232,171,67,.14) 45%, transparent 80%);
      filter: blur(16px);
    }

    .mini, .sprite, .px, .bar {
      display: none !important;
    }
    /* TITAN_PREVIEW_MASCOT_END */
'''

new_js = r'''
// TITAN_PREVIEW_MASCOT_JS_START
window.addEventListener("DOMContentLoaded", () => {
  const faces = Array.from(document.querySelectorAll(".titan-face"));

  function blinkAll(duration = 170) {
    faces.forEach(face => face.classList.add("blink"));
    setTimeout(() => {
      faces.forEach(face => face.classList.remove("blink"));
    }, duration);
  }

  function doubleBlink() {
    blinkAll(170);
    setTimeout(() => blinkAll(150), 240);
  }

  /* quick startup blink so you know it works */
  setTimeout(() => blinkAll(180), 900);

  /* more visible than every 30 sec */
  setInterval(() => {
    if (Math.random() < 0.35) {
      doubleBlink();
    } else {
      blinkAll(180);
    }
  }, 12000);

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
      const mx = dx * 1.0 * scale;
      const my = dy * 0.75 * scale;

      face.querySelectorAll(".eye-core").forEach(eye => {
        eye.style.transform = `translate(${mx}px, ${my}px)`;
      });
    });
  });
});
// TITAN_PREVIEW_MASCOT_JS_END
'''

text = re.sub(
    r'/\* TITAN_PREVIEW_MASCOT_START \*/.*?/\* TITAN_PREVIEW_MASCOT_END \*/',
    new_css,
    text,
    flags=re.S
)

text = re.sub(
    r'// TITAN_PREVIEW_MASCOT_JS_START.*?// TITAN_PREVIEW_MASCOT_JS_END',
    new_js,
    text,
    flags=re.S
)

path.write_text(text, encoding="utf-8")
print("Patched Titan mascot: smaller eyes, visible blink, more 3D pop.")
