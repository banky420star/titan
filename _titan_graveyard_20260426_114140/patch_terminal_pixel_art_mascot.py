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

    # Pixel-cell colours.
    colors = {
        ".": None,
        "Y": "#F8E45C",
        "y": "#DDBB24",
        "O": "#F6A623",
        "o": "#D97817",
        "R": "#EF7C73",
        "r": "#C94C4C",
        "B": "#0F172A",
        "W": "#FFFFFF",
        "S": "#CBD5E1",
    }

    # Pixel-art Titan.
    # Y = yellow block, O = orange block, R = coral block
    # B/W/S = eye and shine pixels
    if open_eyes:
        rows = [
            "........OOOOO........",
            ".......OOOOOOO.......",
            ".......OOOOOOO.......",
            "....YYYYOOOOOOORRR...",
            "...YYYYYOOOOOOORRRR..",
            "..YYYYYYOOBWOOOBWRRR.",
            "..YYYYYYOOBBOOOBBRRR.",
            ".YYYYYYYOOOOOOORRRRR.",
            ".YYYYYYYOOOBOOORRRRR.",
            "..YYYYYYOOOBBOORRRR..",
            "...YYYYYOOOOOOORRR...",
            "....YYY..OOO..RRR....",
            "....YY...OOO...RR....",
            ".........ooo.........",
        ]
    else:
        rows = [
            "........OOOOO........",
            ".......OOOOOOO.......",
            ".......OOOOOOO.......",
            "....YYYYOOOOOOORRR...",
            "...YYYYYOOOOOOORRRR..",
            "..YYYYYYOOBBBOOBBBRR.",
            "..YYYYYYOOOOOOORRRRR.",
            ".YYYYYYYOOOOOOORRRRR.",
            ".YYYYYYYOOOBOOORRRRR.",
            "..YYYYYYOOOBBOORRRR..",
            "...YYYYYOOOOOOORRR...",
            "....YYY..OOO..RRR....",
            "....YY...OOO...RR....",
            ".........ooo.........",
        ]

    logo.append("\n")

    for row in rows:
        logo.append("      ")
        for cell in row:
            color = colors.get(cell)
            if color:
                logo.append("  ", style=f"on {color}")
            else:
                logo.append("  ")
        logo.append("\n")

    logo.append("\n")
    return logo

'''

text = text[:start] + new_logo + text[end:]
path.write_text(text)

print("Installed pixel-art Titan mascot in terminal header.")
