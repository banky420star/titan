from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text()

# Replace titan_logo_text()
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

    yellow = "on #E8DD69"
    orange = "on #E8AB43"
    coral = "on #DD867B"
    pupil = "bold #0F172A"
    shine = "bold #C7CDD8"

    logo.append("\n")

    # top cap of taller middle bar
    seg("                    ")
    seg("        ", orange)
    logo.append("\n")

    # top of main body
    seg("            ")
    seg("      ", yellow)
    seg("        ", orange)
    seg("      ", coral)
    logo.append("\n")

    # wider middle body
    seg("          ")
    seg("        ", yellow)
    seg("        ", orange)
    seg("        ", coral)
    logo.append("\n")

    # eyes row
    seg("          ")
    seg("        ", yellow)

    if open_eyes:
        seg("  ", orange)
        seg("●", pupil + " " + orange)
        seg("•", shine + " " + orange)
        seg("   ", orange)

        seg("  ", coral)
        seg("●", pupil + " " + coral)
        seg("•", shine + " " + coral)
        seg("   ", coral)
    else:
        seg("  ━━   ", pupil + " " + orange)
        seg("  ━━   ", pupil + " " + coral)

    logo.append("\n")

    # lower main body
    seg("          ")
    seg("        ", yellow)
    seg("        ", orange)
    seg("        ", coral)
    logo.append("\n")

    # bottom taper
    seg("            ")
    seg("      ", yellow)
    seg("        ", orange)
    seg("      ", coral)
    logo.append("\n")

    # bottom cap of taller middle bar
    seg("                    ")
    seg("        ", orange)
    logo.append("\n\n")

    return logo

'''

text = text[:start] + new_logo + text[end:]

# Replace titan_prompt()
start = text.find("def titan_prompt():")
if start == -1:
    raise SystemExit("Could not find titan_prompt()")

end = text.find("\ndef startup():", start)
if end == -1:
    raise SystemExit("Could not find startup() after titan_prompt()")

new_prompt = r'''def titan_prompt():
    reset = "\033[0m"

    yellow = "\033[48;2;232;221;105m  " + reset

    orange_eye = (
        "\033[48;2;232;171;67m"
        "\033[38;2;15;23;42m●"
        "\033[38;2;199;205;216m•"
        + reset
    )

    coral_eye = (
        "\033[48;2;221;134;123m"
        "\033[38;2;15;23;42m●"
        "\033[38;2;199;205;216m•"
        + reset
    )

    return f"\n{yellow}{orange_eye}{coral_eye} titan ▸ "

'''

text = text[:start] + new_prompt + text[end:]

path.write_text(text)
print("Patched Titan terminal mascot to match the real icon.")
