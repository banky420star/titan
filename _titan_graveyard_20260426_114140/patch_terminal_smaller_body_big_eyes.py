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

    # Smaller Titan body so the eyes feel larger.
    # Shape: short yellow, tall orange, short coral.

    # tall orange top
    seg("              ")
    seg("      ", orange)
    logo.append("\n")

    seg("              ")
    seg("      ", orange)
    logo.append("\n")

    # upper body
    seg("        ")
    seg("    ", yellow)
    seg("      ", orange)
    seg("    ", coral)
    logo.append("\n")

    seg("      ")
    seg("      ", yellow)
    seg("      ", orange)
    seg("      ", coral)
    logo.append("\n")

    # eye row: same large eyes, smaller body
    seg("      ")
    seg("      ", yellow)

    if open_eyes:
        seg(" ", orange)
        seg("⬤", pupil + " " + orange)
        seg("•", shine + " " + orange)
        seg(" ", orange)

        seg(" ", coral)
        seg("⬤", pupil + " " + coral)
        seg("•", shine + " " + coral)
        seg(" ", coral)
    else:
        seg(" ━━ ", pupil + " " + orange)
        seg(" ━━ ", pupil + " " + coral)

    logo.append("\n")

    # lower body
    seg("      ")
    seg("      ", yellow)
    seg("      ", orange)
    seg("      ", coral)
    logo.append("\n")

    seg("        ")
    seg("    ", yellow)
    seg("      ", orange)
    seg("    ", coral)
    logo.append("\n")

    # tall orange bottom
    seg("              ")
    seg("      ", orange)
    logo.append("\n")

    logo.append("\n")
    return logo

'''

text = text[:start] + new_logo + text[end:]
path.write_text(text)

print("Patched header mascot: smaller body, bigger-looking eyes.")
