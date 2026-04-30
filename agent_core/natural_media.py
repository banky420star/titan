import json
import re


IMAGE_PREFIXES = [
    "create image",
    "create an image",
    "create a image",
    "create me an image",
    "create me a image",
    "make image",
    "make an image",
    "make a image",
    "make me an image",
    "make me a image",
    "generate image",
    "generate an image",
    "generate a image",
    "draw",
    "draw me",
    "create picture",
    "create a picture",
    "create me a picture",
    "make picture",
    "make a picture",
    "make me a picture",
    "generate picture",
    "generate a picture",
]

VIDEO_PREFIXES = [
    "create video",
    "create a video",
    "make video",
    "make a video",
    "generate video",
    "generate a video",
    "create mp4",
    "make mp4",
]


GIF_PREFIXES = [
    "create gif",
    "create a gif",
    "create short gif",
    "create a short gif",
    "make gif",
    "make a gif",
    "make short gif",
    "make a short gif",
    "generate gif",
    "generate a gif",
    "animate",
    "create animation",
    "make animation",
]


def clean_prompt(text):
    text = str(text or "").strip()
    text = re.sub(r"^(of|for|showing|with|about)\s+", "", text, flags=re.I)
    return text.strip()


def strip_prefix(command, prefixes):
    low = command.lower().strip()

    for prefix in sorted(prefixes, key=len, reverse=True):
        if low == prefix:
            return ""
        if low.startswith(prefix + " "):
            return clean_prompt(command[len(prefix):])

    return None


def route_natural_media(command):
    command = str(command or "").strip()

    if not command:
        return None

    image_prompt = strip_prefix(command, IMAGE_PREFIXES)
    if image_prompt is not None:
        if not image_prompt:
            return {
                "handled": True,
                "text": "Usage: create image <what you want to see>"
            }

        from agent_core.image_tools import create_image
        result = create_image(image_prompt)
        return {
            "handled": True,
            "text": json.dumps(result, indent=2)
        }

    video_prompt = strip_prefix(command, VIDEO_PREFIXES)
    if video_prompt is not None:
        if not video_prompt:
            return {
                "handled": True,
                "text": "Usage: create video <what should move>"
            }

        from agent_core.video_tools import create_video
        result = create_video(video_prompt)
        return {
            "handled": True,
            "text": json.dumps(result, indent=2)
        }

    gif_prompt = strip_prefix(command, GIF_PREFIXES)
    if gif_prompt is not None:
        if not gif_prompt:
            return {
                "handled": True,
                "text": "Usage: create gif <what should move>"
            }

        from agent_core.image_tools import create_gif
        result = create_gif(gif_prompt)
        return {
            "handled": True,
            "text": json.dumps(result, indent=2)
        }

    low = command.lower().strip()

    if low in ["show videos", "list videos", "my videos", "open videos"]:
        from agent_core.video_tools import list_videos
        return {
            "handled": True,
            "text": json.dumps(list_videos(), indent=2)
        }

    if low in ["show images", "list images", "my images", "open images"]:
        from agent_core.image_tools import list_images
        return {
            "handled": True,
            "text": json.dumps(list_images(), indent=2)
        }

    return None
