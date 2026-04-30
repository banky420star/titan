from pathlib import Path
import re

path = Path("control_panel.py")
text = path.read_text()

Path("backups").mkdir(exist_ok=True)
Path("backups/control_panel_before_character_fix.py").write_text(text)

# 1. Replace sidebar mini mascot.
mini_html = '''<div class="titan-logo mini-logo">
          <div class="chunk y"></div>
          <div class="chunk o"><span class="eye"></span></div>
          <div class="chunk r"><span class="eye"></span></div>
        </div>'''

text = re.sub(
    r'<div class="mini">\s*<div class="bar y"></div><div class="bar o"></div><div class="bar r"></div>\s*</div>',
    mini_html,
    text,
    flags=re.S
)

# 2. Replace broken hero sprite mascot.
hero_html = '''<div class="titan-logo hero-logo" id="titanMascot">
                <div class="chunk y"></div>
                <div class="chunk o"><span class="eye"></span></div>
                <div class="chunk r"><span class="eye"></span></div>
              </div>'''

text = re.sub(
    r'<div class="mascot">\s*<div class="sprite" id="sprite"></div>\s*</div>',
    '<div class="mascot">\n              ' + hero_html + '\n            </div>',
    text,
    flags=re.S
)

# 3. Add clean mascot CSS overrides before </style>.
css = r'''
    /* TITAN_CHARACTER_FIX */
    .titan-logo {
      display: flex;
      align-items: flex-end;
      justify-content: center;
      position: relative;
      filter: drop-shadow(0 14px 24px rgba(0,0,0,.28));
    }

    .titan-logo .chunk {
      position: relative;
      display: block;
      box-shadow:
        inset 7px 9px 12px rgba(255,255,255,.22),
        inset -7px -10px 14px rgba(0,0,0,.16);
      transition: transform .16s ease;
    }

    .titan-logo .chunk.y {
      background: linear-gradient(145deg, #fff06a, #e8dd69);
    }

    .titan-logo .chunk.o {
      background: linear-gradient(145deg, #ffc46b, #e8ab43);
      z-index: 2;
    }

    .titan-logo .chunk.r {
      background: linear-gradient(145deg, #ff7b7d, #dd867b);
      z-index: 1;
    }

    .hero-logo {
      width: 142px;
      height: 142px;
      animation: titanFloat 3.4s ease-in-out infinite;
    }

    .hero-logo .chunk.y {
      width: 44px;
      height: 70px;
      border-radius: 17px;
      margin-right: -7px;
    }

    .hero-logo .chunk.o {
      width: 48px;
      height: 112px;
      border-radius: 18px;
    }

    .hero-logo .chunk.r {
      width: 44px;
      height: 78px;
      border-radius: 17px;
      margin-left: -7px;
    }

    .mini-logo {
      width: 38px;
      height: 38px;
      gap: 0;
      filter: drop-shadow(0 8px 12px rgba(0,0,0,.22));
    }

    .mini-logo .chunk.y {
      width: 12px;
      height: 24px;
      border-radius: 6px;
      margin-right: -2px;
    }

    .mini-logo .chunk.o {
      width: 14px;
      height: 36px;
      border-radius: 7px;
    }

    .mini-logo .chunk.r {
      width: 12px;
      height: 27px;
      border-radius: 6px;
      margin-left: -2px;
    }

    .titan-logo .eye {
      position: absolute;
      display: block;
      background: #0f172a;
      border-radius: 999px;
      transform-origin: center;
      transition: transform .1s ease;
    }

    .hero-logo .eye {
      width: 13px;
      height: 19px;
      top: 49px;
      box-shadow: inset -2px -3px 4px rgba(0,0,0,.2);
    }

    .hero-logo .chunk.o .eye {
      right: 9px;
    }

    .hero-logo .chunk.r .eye {
      left: 9px;
      top: 31px;
    }

    .mini-logo .eye {
      width: 5px;
      height: 8px;
      top: 13px;
    }

    .mini-logo .chunk.o .eye {
      right: 3px;
    }

    .mini-logo .chunk.r .eye {
      left: 3px;
      top: 10px;
    }

    .titan-logo .eye::after {
      content: "";
      position: absolute;
      width: 28%;
      height: 28%;
      border-radius: 50%;
      background: white;
      left: 28%;
      top: 18%;
      opacity: .95;
    }

    .titan-logo.blink .eye {
      transform: scaleY(.12);
    }

    .titan-logo:hover .chunk.o {
      transform: translateY(-3px);
    }

    @keyframes titanFloat {
      50% { transform: translateY(-7px); }
    }

    /* Hide old pixel sprite pieces if any remain */
    .sprite,
    .px {
      display: none !important;
    }
'''

if "TITAN_CHARACTER_FIX" not in text:
    text = text.replace("</style>", css + "\n  </style>")

# 4. Remove broken sprite JavaScript and replace with clean blink + mouse movement.
start = text.find("const spriteRows = [")
end = text.find("function showView", start)

new_js = r'''const titanMascot = document.getElementById("titanMascot");

function blinkTitan() {
  document.querySelectorAll(".titan-logo").forEach(el => el.classList.add("blink"));
  setTimeout(() => {
    document.querySelectorAll(".titan-logo").forEach(el => el.classList.remove("blink"));
  }, 130);
}

setInterval(blinkTitan, 30000);

window.addEventListener("mousemove", event => {
  if (!titanMascot) return;

  const rect = titanMascot.getBoundingClientRect();
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;

  const dx = Math.max(-1, Math.min(1, (event.clientX - cx) / 500));
  const dy = Math.max(-1, Math.min(1, (event.clientY - cy) / 500));

  titanMascot.style.translate = `${dx * 5}px ${dy * 5}px`;
});

'''

if start != -1 and end != -1:
    text = text[:start] + new_js + text[end:]

path.write_text(text)
print("Fixed dashboard Titan character.")
