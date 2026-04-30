from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text()

start = text.find("def titan_logo_text(")
if start == -1:
    raise SystemExit("Could not find titan_logo_text()")

end = text.find("\ndef startup_frame(", start)
if end == -1:
    raise SystemExit("Could not find startup_frame() after titan_logo_text()")

new_logo = r'''def titan_logo_text(open_eyes=True):
    logo = Text()

    def seg(chars, style=""):
        logo.append(chars, style=style)

    yellow = "on #F8E45C"
    orange = "on #F6A623"
    coral = "on #EF7C73"
    eye = "bold #111827"
    shine = "bold white"

    logo.append("\n")

    # Soft top of taller middle bar.
    seg("              ")
    seg("    ", orange)
    logo.append("\n")

    seg("            ")
    seg("        ", orange)
    logo.append("\n")

    # Main rounded-looking body.
    seg("        ")
    seg("      ", yellow)
    seg("        ", orange)
    seg("      ", coral)
    logo.append("\n")

    seg("      ")
    seg("        ", yellow)
    seg("        ", orange)
    seg("        ", coral)
    logo.append("\n")

    # Cute glossy eyes row.
    seg("      ")
    seg("        ", yellow)

    if open_eyes:
        seg("  ", orange)
        seg("●", eye + " " + orange)
        seg("•", shine + " " + orange)
        seg("    ", orange)

        seg("  ", coral)
        seg("●", eye + " " + coral)
        seg("•", shine + " " + coral)
        seg("    ", coral)
    else:
        seg("  ━     ", eye + " " + orange)
        seg("  ━     ", eye + " " + coral)

    logo.append("\n")

    # Lower body rows.
    seg("      ")
    seg("        ", yellow)
    seg("        ", orange)
    seg("        ", coral)
    logo.append("\n")

    seg("      ")
    seg("        ", yellow)
    seg("        ", orange)
    seg("        ", coral)
    logo.append("\n")

    seg("        ")
    seg("      ", yellow)
    seg("        ", orange)
    seg("      ", coral)
    logo.append("\n")

    # Bottom of taller middle bar.
    seg("            ")
    seg("        ", orange)
    logo.append("\n")

    logo.append("\n")
    return logo

'''

text = text[:start] + new_logo + text[end:]

start = text.find("def titan_prompt():")
if start == -1:
    raise SystemExit("Could not find titan_prompt()")

end = text.find("\ndef startup():", start)
if end == -1:
    raise SystemExit("Could not find startup() after titan_prompt()")

new_prompt = r'''def titan_prompt():
    # Tiny version of the same Titan mascot:
    # yellow block + orange glossy eye + coral glossy eye.
    reset = "\033[0m"

    yellow = "\033[48;2;248;228;92m  " + reset

    orange_eye = (
        "\033[48;2;246;166;35m"
        "\033[38;2;17;24;39m●"
        "\033[38;2;255;255;255m·"
        + reset
    )

    coral_eye = (
        "\033[48;2;239;124;115m"
        "\033[38;2;17;24;39m●"
        "\033[38;2;255;255;255m·"
        + reset
    )

    return f"\n{yellow}{orange_eye}{coral_eye} titan ▸ "

'''

text = text[:start] + new_prompt + text[end:]

path.write_text(text)
print("Patched Titan terminal icon to be cuter and closer to the real mascot.")
