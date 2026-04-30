from pathlib import Path

path = Path("control_panel.py")
text = path.read_text(encoding="utf-8")

backup = Path("backups/control_panel_before_eye_tweak.py")
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

replacements = {
    # BIG mascot eyes
    """.titan-mascot-lg .eye-wrap {
      width: 14px;
      height: 22px;
      top: 45px;
    }""": """.titan-mascot-lg .eye-wrap {
      width: 20px;
      height: 30px;
      top: 52px;
    }""",

    """.titan-mascot-lg .eye-left {
      left: 50px;
    }""": """.titan-mascot-lg .eye-left {
      left: 46px;
    }""",

    """.titan-mascot-lg .eye-right {
      left: 68px;
    }""": """.titan-mascot-lg .eye-right {
      left: 66px;
    }""",

    # SMALL sidebar mascot eyes
    """.titan-mascot-sm .eye-wrap {
      width: 5px;
      height: 9px;
      top: 17px;
    }""": """.titan-mascot-sm .eye-wrap {
      width: 7px;
      height: 12px;
      top: 19px;
    }""",

    """.titan-mascot-sm .eye-left {
      left: 17px;
    }""": """.titan-mascot-sm .eye-left {
      left: 15px;
    }""",

    """.titan-mascot-sm .eye-right {
      left: 24px;
    }""": """.titan-mascot-sm .eye-right {
      left: 23px;
    }""",

    # slightly larger eye shine so it still looks cute
    """.titan-face .eye-core::after {
      content: "";
      position: absolute;
      width: 30%;
      height: 30%;
      left: 27%;
      top: 15%;
      border-radius: 50%;
      background: rgba(255,255,255,.98);
    }""": """.titan-face .eye-core::after {
      content: "";
      position: absolute;
      width: 32%;
      height: 32%;
      left: 25%;
      top: 14%;
      border-radius: 50%;
      background: rgba(255,255,255,.98);
    }""",
}

changed = 0
for old, new in replacements.items():
    if old in text:
        text = text.replace(old, new)
        changed += 1

path.write_text(text, encoding="utf-8")
print(f"Patched control_panel.py. Replacements applied: {changed}")
