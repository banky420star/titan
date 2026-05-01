from pathlib import Path
from PIL import Image

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
WORKSPACE = BASE / "workspace"
DOWNLOADS = BASE / "downloads"


def upscale_image(src, scale=2):
    src = Path(src)

    # Resolve workspace-relative and download-relative paths
    if not src.is_absolute():
        for root in [WORKSPACE, DOWNLOADS, BASE]:
            candidate = root / src
            if candidate.exists():
                src = candidate
                break

    if not src.exists():
        return {"error": f"File not found: {src}"}

    img = Image.open(src)
    out = src.with_name(src.stem + f"_x{scale}" + src.suffix)
    img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    img.save(out)
    return {"result": "upscaled", "path": str(out), "scale": scale}