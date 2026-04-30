from pathlib import Path

path = Path("agent_core/natural_media.py")

if not path.exists():
    path.write_text('''import json\n\n\ndef route_natural_media(command):\n    return None\n''', encoding="utf-8")

text = path.read_text(encoding="utf-8")

backup = Path("backups/natural_media_before_video_patch.py")
backup.parent.mkdir(exist_ok=True)
backup.write_text(text, encoding="utf-8")

if "VIDEO_PREFIXES" not in text:
    text = text.replace(
        "GIF_PREFIXES = [",
        '''VIDEO_PREFIXES = [
    "create video",
    "create a video",
    "make video",
    "make a video",
    "generate video",
    "generate a video",
    "create mp4",
    "make mp4",
]


GIF_PREFIXES = ['''
    )

if "video_prompt = strip_prefix(command, VIDEO_PREFIXES)" not in text:
    marker = "gif_prompt = strip_prefix(command, GIF_PREFIXES)"
    insert = '''video_prompt = strip_prefix(command, VIDEO_PREFIXES)
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

    '''
    text = text.replace(marker, insert + marker, 1)

if '"show videos"' not in text:
    text = text.replace(
        '''if low in ["show images", "list images", "my images", "open images"]:''',
        '''if low in ["show videos", "list videos", "my videos", "open videos"]:
        from agent_core.video_tools import list_videos
        return {
            "handled": True,
            "text": json.dumps(list_videos(), indent=2)
        }

    if low in ["show images", "list images", "my images", "open images"]:'''
    )

path.write_text(text, encoding="utf-8")
print("Natural video routing installed.")
