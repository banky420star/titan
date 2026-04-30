from pathlib import Path
from PIL import Image

def upscale_image(src, scale=2):
    src = Path(src)
    if not src.exists():
        return {"error": f"File not found: {src}"}

    img = Image.open(src)
    out = src.with_name(src.stem + f"_x{scale}" + src.suffix)
    img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    img.save(out)
    return {"result": "upscaled", "path": str(out), "scale": scale}
