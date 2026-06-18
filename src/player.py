"""Launches local media (video or photo slideshow) fullscreen on the TV.

Uses mpv because it is lightweight, scriptable, handles both video and
image slideshows, and runs well on a Raspberry Pi without a desktop
environment.
"""
import glob
import logging
import os
import subprocess

from . import config

logger = logging.getLogger(__name__)

_current_process = None


def stop():
    """Stop whatever is currently playing (e.g. before starting something new)."""
    global _current_process
    if _current_process and _current_process.poll() is None:
        _current_process.terminate()
    _current_process = None


def _resolve(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(config.CONTENT_DIR, path)


def play_video(path: str):
    """Play a single video file fullscreen."""
    stop()
    full_path = _resolve(path)
    if not os.path.exists(full_path):
        logger.error("Video not found: %s", full_path)
        return

    global _current_process
    _current_process = subprocess.Popen(
        [config.MPV_BINARY, "--fullscreen", "--no-terminal", full_path]
    )


def play_slideshow(folder: str, video: str = None):
    """Show every photo in a folder as a slideshow, then optionally play a
    closing video clip (e.g. a short clip filmed at that location)."""
    stop()
    full_folder = _resolve(folder)
    images = sorted(
        glob.glob(os.path.join(full_folder, "*.jpg"))
        + glob.glob(os.path.join(full_folder, "*.jpeg"))
        + glob.glob(os.path.join(full_folder, "*.png"))
    )

    if not images:
        logger.warning("No images found in %s", full_folder)
    else:
        global _current_process
        _current_process = subprocess.Popen(
            [
                config.MPV_BINARY,
                "--fullscreen",
                "--no-terminal",
                f"--image-display-duration={config.SLIDESHOW_IMAGE_DURATION}",
                *images,
            ]
        )
        _current_process.wait()  # block until the slideshow finishes

    if video:
        play_video(video)
