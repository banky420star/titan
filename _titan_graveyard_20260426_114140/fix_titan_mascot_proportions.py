from pathlib import Path
import re

path = Path("control_panel.py")
text = path.read_text(encoding="utf-8")

Path("backups").mkdir(exist_ok=True)
Path("backups/control_panel_before_mascot_proportion_fix.py").write_text(text, encoding="utf-8")

# Replace only the mascot CSS block.
css = r'''
    /* TITAN_PREVIEW_MASCOT_START */
    .titan-mascot {
      position: relative;
      display: inline-block;
      user-select: none;
      filter: drop-shadow(0 14px 24px rgba(0,0,0,.28));
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
      background: linear-gradient(180deg, #fff17a 0%, #f6e363 42%, #e8dc67 100%);
    }

    .titan-mascot .seg-o {
      background: linear-gradient(180deg, #ffd08a 0%, #f7b653 42%, #e8ab43 100%);
      z-index: 2;
    }

    .titan-mascot .seg-r {
      background: linear-gradient(180deg, #f8a7a0 0%, #ef8e87 42%, #dd867b 100%);
      z-index: 1;
    }

    /*
      Correct hero proportions:
      - yellow short left bar
      - orange tall middle bar
      - coral short right bar
      - all bottoms aligned
      - eyes lower and centered like the approved preview
    */
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
      filter: drop-shadow(0 6px 12px rgba(0,0,0,.22));
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
      transition: transform .12s ease;
    }

    .titan-mascot-lg .eye-wrap {
      width: 14px;
      height: 22px;
      top: 45px;
    }

    .titan-mascot-lg .eye-left {
      left: 50px;
    }

    .titan-mascot-lg .eye-right {
      left: 68px;
    }

    .titan-mascot-sm .eye-wrap {
      width: 5px;
      height: 9px;
      top: 17px;
    }

    .titan-mascot-sm .eye-left {
      left: 17px;
    }

    .titan-mascot-sm .eye-right {
      left: 24px;
    }

    .titan-face .eye-core {
      position: absolute;
      inset: 0;
      border-radius: 999px;
      background: radial-gradient(circle at 35% 26%, #173063 0%, #091335 58%, #030817 100%);
      box-shadow:
        inset -1px -2px 3px rgba(0,0,0,.25),
        0 1px 2px rgba(0,0,0,.18);
      transform: translate(0px, 0px);
      transition: transform .08s linear;
    }

    .titan-face .eye-core::after {
      content: "";
      position: absolute;
      width: 30%;
      height: 30%;
      left: 27%;
      top: 15%;
      border-radius: 50%;
      background: rgba(255,255,255,.98);
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
      width: 105px;
      height: 28px;
      bottom: 22px;
      border-radius: 50%;
      background: rgba(232,171,67,.22);
      filter: blur(16px);
    }

    .mini, .sprite, .px, .bar {
      display: none !important;
    }
    /* TITAN_PREVIEW_MASCOT_END */
'''

text = re.sub(
    r'/\* TITAN_PREVIEW_MASCOT_START \*/.*?/\* TITAN_PREVIEW_MASCOT_END \*/',
    css,
    text,
    flags=re.S
)

# Make sure eye tracking is not over-moving the eyes.
text = re.sub(
    r'const mx = dx \* [0-9.]+ \* scale;\s*const my = dy \* [0-9.]+ \* scale;',
    'const mx = dx * 1.15 * scale;\n      const my = dy * 0.8 * scale;',
    text
)

path.write_text(text, encoding="utf-8")
print("Fixed Titan mascot proportions.")
