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

    # Taller center bar top
    seg("                    ")
    seg("        ", orange)
    logo.append("\n")

    # Upper body
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

    # EYES ROW - much larger single glossy eye per side
    seg("          ")
    seg("        ", yellow)

    if open_eyes:
        # orange eye
        seg(" ", orange)
        seg("⬤", pupil + " " + orange)
        seg("•", shine + " " + orange)
        seg("  ", orange)

        # coral eye
        seg(" ", coral)
        seg("⬤", pupil + " " + coral)
        seg("•", shine + " " + coral)
        seg("  ", coral)
    else:
        seg(" ━━━  ", pupil + " " + orange)
        seg(" ━━━  ", pupil + " " + coral)

    logo.append("\n")

    # Add one more face row so the eyes feel taller/bigger like the mascot
    seg("          ")
    seg("        ", yellow)

    if open_eyes:
        seg(" ", orange)
        seg("⬤", pupil + " " + orange)
        seg(" ", orange)
        seg("  ", orange)

        seg(" ", coral)
        seg("⬤", pupil + " " + coral)
        seg(" ", coral)
        seg("  ", coral)
    else:
        seg(" ━━━  ", pupil + " " + orange)
        seg(" ━━━  ", pupil + " " + coral)

    logo.append("\n")

    # Lower body
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

    # Taller center bar bottom
    seg("                    ")
    seg("        ", orange)
    logo.append("\n\n")

    return logo

'''

text = text[:start] + new_logo + text[end:]
path.write_text(text)
print("Patched big startup mascot with much larger eyes.")
