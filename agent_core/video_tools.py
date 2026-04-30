"""Video tools — thin wrapper around media_engine."""

from agent_core.media_engine import (
    create_video as _create_video,
    list_videos,
    set_video_quality,
    set_video_motion,
    set_video_image_backend,
    video_status,
    nsfw_enabled,
    clean_prompt,
    VIDEO_OUT,
)

# Ensure output dir exists
VIDEO_OUT.mkdir(parents=True, exist_ok=True)


def create_video(prompt, seconds=8, fps=24, open_file=True):
    """Generate a video using the unified media engine."""
    return _create_video(prompt, seconds=seconds, fps=fps, open_file=open_file, nsfw=False)


def create_explicit_video(prompt, seconds=10, fps=24):
    """Generate an NSFW video using the unified media engine."""
    return _create_video(prompt, seconds=seconds, fps=fps, open_file=True, nsfw=True)


print("video_tools ready")