from pathlib import Path

path = Path("control_panel_titan_ui.py")
if not path.exists():
    path = Path("control_panel.py")

if not path.exists():
    raise SystemExit("Could not find control_panel_titan_ui.py or control_panel.py")

text = path.read_text()

marker = "</style>"
if marker not in text:
    raise SystemExit("Could not find </style>")

simple_css = r'''
    /* SIMPLE TITAN DESIGN OVERRIDE */
    body {
      background:
        radial-gradient(circle at 50% 8%, rgba(255, 180, 90, 0.08), transparent 26%),
        linear-gradient(180deg, #121315 0%, #18191c 100%) !important;
    }

    .app {
      grid-template-columns: 300px 1fr !important;
    }

    .sidebar {
      background: #111214 !important;
      border-right: 1px solid rgba(255,255,255,0.07) !important;
      box-shadow: none !important;
    }

    .main {
      padding: 54px 56px !important;
    }

    .content {
      max-width: 980px !important;
    }

    .hero {
      grid-template-columns: 120px 1fr !important;
      gap: 26px !important;
      align-items: center !important;
      margin-bottom: 24px !important;
    }

    .mascot-stage {
      width: 120px !important;
      height: 120px !important;
    }

    .mascot-glow {
      width: 120px !important;
      height: 58px !important;
      bottom: 4px !important;
      opacity: 0.45 !important;
      filter: blur(10px) !important;
    }

    .sparkle {
      display: none !important;
    }

    h1 {
      font-size: 58px !important;
      letter-spacing: -0.055em !important;
      line-height: 1 !important;
    }

    .subtitle {
      font-size: 19px !important;
      line-height: 1.45 !important;
      color: #a9abb3 !important;
      margin-top: 10px !important;
    }

    .private {
      font-size: 15px !important;
      padding: 7px 12px !important;
      background: rgba(255,255,255,0.07) !important;
      border-color: rgba(255,255,255,0.08) !important;
      color: #d4d4d8 !important;
    }

    .prompt {
      height: 68px !important;
      margin-top: 26px !important;
      margin-bottom: 30px !important;
      background: rgba(255,255,255,0.055) !important;
      border: 1px solid rgba(255,255,255,0.08) !important;
      box-shadow: none !important;
    }

    .prompt input {
      font-size: 19px !important;
    }

    .send {
      width: 46px !important;
      height: 46px !important;
      background: rgba(255,255,255,0.10) !important;
      box-shadow: none !important;
    }

    .card-grid {
      grid-template-columns: repeat(4, 1fr) !important;
      gap: 16px !important;
    }

    .quick-card {
      min-height: 150px !important;
      padding: 20px !important;
      border-radius: 20px !important;
      background: rgba(255,255,255,0.045) !important;
      border: 1px solid rgba(255,255,255,0.075) !important;
      box-shadow: none !important;
    }

    .quick-card:hover {
      transform: translateY(-2px) !important;
      background: rgba(255,255,255,0.065) !important;
      border-color: rgba(255,255,255,0.12) !important;
    }

    .card-icon {
      width: 42px !important;
      height: 42px !important;
      border-radius: 14px !important;
      font-size: 20px !important;
      margin-bottom: 16px !important;
      background: rgba(255,255,255,0.07) !important;
    }

    .quick-card h3 {
      font-size: 16px !important;
      margin-bottom: 7px !important;
    }

    .quick-card p {
      font-size: 14px !important;
      line-height: 1.42 !important;
    }

    .arrow {
      font-size: 20px !important;
    }

    .activity {
      margin-top: 20px !important;
      border-radius: 22px !important;
      background: rgba(255,255,255,0.04) !important;
      border: 1px solid rgba(255,255,255,0.075) !important;
      box-shadow: none !important;
    }

    /* SIMPLER TITAN CHARACTER */
    .titan-mascot {
      width: 118px !important;
      height: 118px !important;
    }

    .titan-character {
      width: 104px !important;
      height: 112px !important;
      filter:
        drop-shadow(0 14px 22px rgba(0,0,0,0.30))
        drop-shadow(0 0 14px rgba(251,146,60,0.16)) !important;
    }

    .titan-head {
      left: 14px !important;
      top: 18px !important;
      width: 76px !important;
      height: 72px !important;
      border-radius: 28px 28px 26px 26px !important;
      background:
        radial-gradient(circle at 30% 18%, rgba(255,255,255,0.45), transparent 28%),
        linear-gradient(145deg, #ffe66d 0%, #fb923c 50%, #fb7185 100%) !important;
      box-shadow:
        inset -8px -10px 15px rgba(0,0,0,0.16),
        inset 8px 9px 15px rgba(255,255,255,0.24),
        0 12px 22px rgba(0,0,0,0.24) !important;
    }

    .titan-head::after,
    .titan-gloss {
      opacity: 0.7 !important;
    }

    .titan-body {
      left: 24px !important;
      top: 78px !important;
      width: 56px !important;
      height: 32px !important;
      border-radius: 18px 18px 24px 24px !important;
      background: linear-gradient(145deg, #ffb35c, #fb7185) !important;
    }

    .titan-ear {
      display: none !important;
    }

    .titan-arm {
      top: 82px !important;
      width: 12px !important;
      height: 25px !important;
      opacity: 0.9 !important;
    }

    .arm-left {
      left: 14px !important;
    }

    .arm-right {
      right: 14px !important;
    }

    .titan-foot {
      width: 22px !important;
      height: 11px !important;
      bottom: 0 !important;
    }

    .foot-left {
      left: 29px !important;
    }

    .foot-right {
      right: 29px !important;
    }

    .titan-antenna {
      left: 45px !important;
      top: 0 !important;
      transform: scale(0.82) !important;
    }

    .titan-mascot .eye {
      width: 17px !important;
      height: 23px !important;
      top: 29px !important;
    }

    .titan-mascot .eye.left {
      left: 18px !important;
    }

    .titan-mascot .eye.right {
      right: 18px !important;
    }

    .titan-mascot .pupil {
      width: 5px !important;
      height: 7px !important;
      left: 6px !important;
      top: 6px !important;
    }

    .titan-cheek {
      width: 10px !important;
      height: 6px !important;
      top: 52px !important;
    }

    .cheek-left {
      left: 15px !important;
    }

    .cheek-right {
      right: 15px !important;
    }

    .titan-smile {
      left: 31px !important;
      top: 50px !important;
      width: 13px !important;
      height: 8px !important;
    }

    .titan-core {
      left: 20px !important;
      top: 8px !important;
      width: 17px !important;
      height: 17px !important;
      font-size: 9px !important;
    }

    .titan-bubble {
      right: -6px !important;
      top: -4px !important;
      min-width: 28px !important;
      min-height: 28px !important;
      font-size: 13px !important;
    }

    @media (max-width: 1180px) {
      .hero {
        grid-template-columns: 1fr !important;
      }

      .mascot-stage {
        height: 130px !important;
      }

      .card-grid {
        grid-template-columns: repeat(2, 1fr) !important;
      }
    }

    @media (max-width: 700px) {
      .main {
        padding: 28px 18px !important;
      }

      h1 {
        font-size: 44px !important;
      }

      .card-grid {
        grid-template-columns: 1fr !important;
      }
    }
'''

if "/* SIMPLE TITAN DESIGN OVERRIDE */" not in text:
    text = text.replace(marker, simple_css + "\n" + marker)

path.write_text(text)
print(f"Applied simple Titan design override to {path}")
