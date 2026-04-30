from pathlib import Path

path = Path("titan_terminal.py")
text = path.read_text()

start = text.find("def titan_logo_text(")
if start == -1:
    raise SystemExit("Could not find titan_logo_text()")

end = text.find("\ndef startup_frame(", start)
if end == -1:
    raise SystemExit("Could not find startup_frame()")

new_logo = r'''def titan_logo_text(open_eyes=True):
    logo = Text()

    def seg(chars, style=""):
        logo.append(chars, style=style)

    yellow = "on #E8DD69"
    orange = "on #E8AB43"
    coral = "on #DD867B"
    pupil = "bold #0F172A"
    shine = "bold white"

    logo.append("\n")

    # Taller center bar top.
    seg("                    ")
    seg("        ", orange)
    logo.append("\n")

    # Upper body.
    seg("            ")
    seg("      ", yellow)
    seg("        ", orange)
    seg("      ", coral)
    logo.append("\n")

    seg("          ")
    seg("        ", yellow)
    seg("        ", orange)
    seg("        ", coral)
    logo.append("\n")

    # Eyes row:
    # ONE large dark eye per side, with one tiny white shine.
    seg("          ")
    seg("        ", yellow)

    if open_eyes:
        seg("  ", orange)
        seg("⬤", pupil + " " + orange)
        seg("•", shine + " " + orange)
        seg("   ", orange)

        seg("  ", coral)
        seg("⬤", pupil + " " + coral)
        seg("•", shine + " " + coral)
        seg("   ", coral)
    else:
        seg("  ━━   ", pupil + " " + orange)
        seg("  ━━   ", pupil + " " + coral)

    logo.append("\n")

    # Lower body.
    seg("          ")
    seg("        ", yellow)
    seg("        ", orange)
    seg("        ", coral)
    logo.append("\n")

    seg("            ")
    seg("      ", yellow)
    seg("        ", orange)
    seg("      ", coral)
    logo.append("\n")

    # Taller center bar bottom.
    seg("                    ")
    seg("        ", orange)
    logo.append("\n\n")

    return logo

'''

text = text[:start] + new_logo + text[end:]

start = text.find("def titan_prompt():")
if start == -1:
    raise SystemExit("Could not find titan_prompt()")

end = text.find("\ndef startup():", start)
if end == -1:
    raise SystemExit("Could not find startup()")

new_prompt = r'''def titan_prompt():
    reset = "\033[0m"

    yellow = "\033[48;2;232;221;105m  " + reset

    orange_eye = (
        "\033[48;2;232;171;67m"
        "\033[38;2;15;23;42m⬤"
        "\033[38;2;255;255;255m•"
        "\033[48;2;232;171;67m "
        + reset
    )

    coral_eye = (
        "\033[48;2;221;134;123m"
        "\033[38;2;15;23;42m⬤"
        "\033[38;2;255;255;255m•"
        "\033[48;2;221;134;123m "
        + reset
    )

    return f"\n{yellow}{orange_eye}{coral_eye} titan ▸ "

'''

text = text[:start] + new_prompt + text[end:]

path.write_text(text)
print("Fixed Titan eyes: one big glossy eye per side.")
