from pathlib import Path

candidates = [
    Path("control_panel_titan_ui.py"),
    Path("control_panel.py")
]

path = next((p for p in candidates if p.exists()), None)
if path is None:
    raise SystemExit("Could not find control_panel_titan_ui.py or control_panel.py")

text = path.read_text()

# Replace sidebar mini bar-chart logo with a mini Titan character.
text = text.replace(
    '<div class="mini-logo"><span></span><span></span><span></span></div>',
    '<div class="mini-character-logo"><span class="mini-eye left"></span><span class="mini-eye right"></span><span class="mini-mouth"></span></div>'
)

start = text.find('          <div class="mascot-stage">')
if start == -1:
    raise SystemExit("Could not find mascot-stage block")

end_marker = '\n\n          <div>\n            <div class="title-row">'
end = text.find(end_marker, start)
if end == -1:
    raise SystemExit("Could not find end of mascot-stage block")

new_html = r'''          <div class="mascot-stage">
            <div class="mascot-glow character-glow"></div>
            <div class="sparkle s1">✦</div>
            <div class="sparkle s2">✧</div>
            <div class="sparkle s3">✦</div>

            <div class="mascot titan-mascot" id="mascot" aria-label="Titan character mascot">
              <div class="titan-shadow"></div>

              <div class="titan-character">
                <div class="titan-antenna">
                  <span></span>
                </div>

                <div class="titan-ear ear-left"></div>
                <div class="titan-ear ear-right"></div>

                <div class="titan-head">
                  <div class="titan-gloss"></div>

                  <div class="eye left">
                    <span class="pupil"></span>
                  </div>

                  <div class="eye right">
                    <span class="pupil"></span>
                  </div>

                  <div class="titan-cheek cheek-left"></div>
                  <div class="titan-cheek cheek-right"></div>
                  <div class="titan-smile"></div>
                </div>

                <div class="titan-body">
                  <div class="titan-core">✦</div>
                </div>

                <div class="titan-arm arm-left"></div>
                <div class="titan-arm arm-right"></div>
                <div class="titan-foot foot-left"></div>
                <div class="titan-foot foot-right"></div>
              </div>
            </div>
          </div>'''

text = text[:start] + new_html + text[end:]

css_marker = "</style>"
if css_marker not in text:
    raise SystemExit("Could not find </style>")

character_css = r'''
    /* Titan character mascot override */
    .mini-character-logo {
      width: 34px;
      height: 34px;
      border-radius: 13px 13px 15px 15px;
      background:
        radial-gradient(circle at 30% 20%, rgba(255,255,255,0.58), transparent 28%),
        linear-gradient(145deg, #ffe66d 0%, #fb923c 52%, #fb7185 100%);
      position: relative;
      box-shadow:
        inset -5px -7px 10px rgba(0,0,0,0.20),
        inset 5px 6px 10px rgba(255,255,255,0.30),
        0 10px 22px rgba(251, 146, 60, 0.22);
    }

    .mini-character-logo::before {
      content: "";
      position: absolute;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      top: -4px;
      left: 13px;
      background: #fef3c7;
      box-shadow: 0 0 10px rgba(251, 191, 36, 0.55);
    }

    .mini-character-logo .mini-eye {
      position: absolute;
      width: 5px;
      height: 8px;
      border-radius: 999px;
      background: #111827;
      top: 13px;
    }

    .mini-character-logo .mini-eye.left {
      left: 10px;
    }

    .mini-character-logo .mini-eye.right {
      right: 10px;
    }

    .mini-character-logo .mini-mouth {
      position: absolute;
      width: 8px;
      height: 5px;
      left: 13px;
      top: 22px;
      border-bottom: 2px solid #7f1d1d;
      border-radius: 50%;
    }

    .character-glow {
      width: 180px;
      height: 110px;
      bottom: 8px;
      background:
        radial-gradient(circle, rgba(251, 146, 60, 0.42), transparent 62%),
        radial-gradient(circle at 60% 40%, rgba(251, 113, 133, 0.24), transparent 54%);
    }

    .titan-mascot {
      width: 190px;
      height: 175px;
      position: relative;
      display: grid;
      place-items: center;
      animation: titanFloat 3.2s ease-in-out infinite;
    }

    @keyframes titanFloat {
      0%, 100% {
        transform: translateY(0) rotate(-1deg);
      }
      50% {
        transform: translateY(-8px) rotate(1deg);
      }
    }

    .titan-shadow {
      position: absolute;
      width: 122px;
      height: 30px;
      bottom: 4px;
      border-radius: 50%;
      background: rgba(0,0,0,0.36);
      filter: blur(9px);
    }

    .titan-character {
      position: relative;
      width: 150px;
      height: 165px;
      filter:
        drop-shadow(0 22px 32px rgba(0,0,0,0.34))
        drop-shadow(0 0 24px rgba(251, 146, 60, 0.18));
    }

    .titan-antenna {
      position: absolute;
      left: 68px;
      top: 0;
      width: 14px;
      height: 24px;
      z-index: 5;
    }

    .titan-antenna::before {
      content: "";
      position: absolute;
      left: 6px;
      top: 8px;
      width: 2px;
      height: 17px;
      background: linear-gradient(180deg, #fde68a, #fb923c);
      border-radius: 99px;
    }

    .titan-antenna span {
      position: absolute;
      left: 2px;
      top: 0;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: #fef3c7;
      box-shadow:
        0 0 12px rgba(251, 191, 36, 0.72),
        inset 0 1px 2px rgba(255,255,255,0.75);
    }

    .titan-ear {
      position: absolute;
      top: 42px;
      width: 36px;
      height: 42px;
      border-radius: 18px 18px 16px 16px;
      background:
        radial-gradient(circle at 35% 20%, rgba(255,255,255,0.36), transparent 35%),
        linear-gradient(145deg, #ffd166, #fb923c 56%, #ea580c);
      box-shadow:
        inset -6px -8px 12px rgba(0,0,0,0.16),
        inset 6px 8px 12px rgba(255,255,255,0.25);
      z-index: 1;
    }

    .ear-left {
      left: 8px;
      transform: rotate(-12deg);
    }

    .ear-right {
      right: 8px;
      transform: rotate(12deg);
      background:
        radial-gradient(circle at 35% 20%, rgba(255,255,255,0.35), transparent 35%),
        linear-gradient(145deg, #ffb77a, #fb7185 56%, #e11d48);
    }

    .titan-head {
      position: absolute;
      left: 25px;
      top: 28px;
      width: 100px;
      height: 92px;
      border-radius: 38px 38px 34px 34px;
      background:
        radial-gradient(circle at 30% 18%, rgba(255,255,255,0.58), transparent 30%),
        linear-gradient(145deg, #ffe66d 0%, #fb923c 46%, #fb7185 100%);
      box-shadow:
        inset -12px -14px 22px rgba(0,0,0,0.18),
        inset 12px 12px 22px rgba(255,255,255,0.28),
        0 18px 34px rgba(0,0,0,0.28);
      z-index: 3;
      overflow: hidden;
    }

    .titan-head::after {
      content: "";
      position: absolute;
      left: 13px;
      top: 9px;
      width: 34px;
      height: 46px;
      border-radius: 999px;
      background: rgba(255,255,255,0.22);
      filter: blur(1px);
      transform: rotate(18deg);
    }

    .titan-gloss {
      position: absolute;
      right: 12px;
      top: 8px;
      width: 22px;
      height: 45px;
      border-radius: 999px;
      background: rgba(255,255,255,0.20);
      filter: blur(1px);
      transform: rotate(-10deg);
    }

    .titan-body {
      position: absolute;
      left: 33px;
      top: 104px;
      width: 84px;
      height: 54px;
      border-radius: 28px 28px 34px 34px;
      background:
        radial-gradient(circle at 32% 22%, rgba(255,255,255,0.34), transparent 30%),
        linear-gradient(145deg, #ffb35c, #fb7185 70%, #be123c);
      box-shadow:
        inset -9px -10px 16px rgba(0,0,0,0.18),
        inset 9px 10px 16px rgba(255,255,255,0.18),
        0 16px 28px rgba(0,0,0,0.28);
      z-index: 2;
    }

    .titan-core {
      position: absolute;
      left: 31px;
      top: 15px;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background:
        radial-gradient(circle at 35% 30%, #ffffff, #c7d2fe 38%, #6366f1);
      color: #312e81;
      font-size: 12px;
      box-shadow:
        0 0 16px rgba(124, 140, 255, 0.62),
        inset 0 1px 3px rgba(255,255,255,0.65);
    }

    .titan-mascot .eye {
      position: absolute;
      width: 22px;
      height: 30px;
      border-radius: 999px;
      background:
        radial-gradient(circle at 34% 20%, #475569, #111827 54%, #020617);
      box-shadow:
        inset 0 2px 3px rgba(255,255,255,0.22),
        0 5px 10px rgba(0,0,0,0.22);
      z-index: 5;
    }

    .titan-mascot .eye.left {
      left: 24px;
      top: 37px;
    }

    .titan-mascot .eye.right {
      right: 24px;
      top: 37px;
    }

    .titan-mascot .pupil {
      position: absolute;
      left: 8px;
      top: 8px;
      width: 7px;
      height: 9px;
      border-radius: 999px;
      background: white;
      transition: transform 80ms linear;
      box-shadow: 0 0 8px rgba(255,255,255,0.85);
    }

    .titan-cheek {
      position: absolute;
      width: 13px;
      height: 8px;
      border-radius: 50%;
      background: rgba(244, 63, 94, 0.28);
      top: 65px;
      z-index: 5;
      filter: blur(0.2px);
    }

    .cheek-left {
      left: 20px;
    }

    .cheek-right {
      right: 20px;
    }

    .titan-smile {
      position: absolute;
      left: 44px;
      top: 63px;
      width: 15px;
      height: 9px;
      border-bottom: 3px solid #7f1d1d;
      border-radius: 50%;
      z-index: 6;
    }

    .titan-arm {
      position: absolute;
      top: 111px;
      width: 18px;
      height: 38px;
      border-radius: 999px;
      background: linear-gradient(180deg, #ffd166, #fb923c);
      box-shadow:
        inset -4px -5px 8px rgba(0,0,0,0.18),
        inset 3px 4px 8px rgba(255,255,255,0.25);
      z-index: 1;
    }

    .arm-left {
      left: 19px;
      transform: rotate(18deg);
    }

    .arm-right {
      right: 19px;
      transform: rotate(-18deg);
      background: linear-gradient(180deg, #ff9f76, #fb7185);
    }

    .titan-foot {
      position: absolute;
      bottom: 0;
      width: 34px;
      height: 18px;
      border-radius: 999px;
      background: linear-gradient(180deg, #fb7185, #be123c);
      box-shadow: 0 8px 15px rgba(0,0,0,0.28);
      z-index: 1;
    }

    .foot-left {
      left: 41px;
    }

    .foot-right {
      right: 41px;
    }
'''

if "/* Titan character mascot override */" not in text:
    text = text.replace(css_marker, character_css + "\n  " + css_marker)

path.write_text(text)
print(f"Patched Titan character mascot in {path}")
