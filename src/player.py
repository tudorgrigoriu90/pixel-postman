"""Launches local media (video or photo slideshow) fullscreen on the TV.

Uses mpv because it is lightweight, scriptable, handles both video and image
slideshows, and runs well on a Raspberry Pi without a desktop environment.

All playback goes through a single, lock-protected current process so the two
listener threads (QR + NFC) can never start mpv on top of each other. Starting
anything new cleanly stops whatever was playing first. A persistent "idle"
image is shown whenever nothing else is playing, so the child never sees a
Linux console.
"""
import glob
import logging
import os
import subprocess
import threading

from . import config

logger = logging.getLogger(__name__)

_lock = threading.RLock()
_proc = None
_mode = None  # None | "idle" | "content"


def _base_flags():
    flags = ["--fullscreen", "--no-terminal", "--no-input-default-bindings"]
    if config.MPV_VIDEO_OUTPUT:
        flags.append(f"--vo={config.MPV_VIDEO_OUTPUT}")
    if config.MPV_GPU_CONTEXT:
        flags.append(f"--gpu-context={config.MPV_GPU_CONTEXT}")
    return flags


def _resolve(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(config.CONTENT_DIR, path)


def _stop_locked():
    global _proc, _mode
    if _proc is not None and _proc.poll() is None:
        _proc.terminate()
        try:
            _proc.wait(timeout=2)
        except subprocess.TimeoutExpired:  # pragma: no cover - rare
            _proc.kill()
    _proc = None
    _mode = None


def _start(args, mode):
    global _proc, _mode
    with _lock:
        _stop_locked()
        _proc = subprocess.Popen([config.MPV_BINARY, *_base_flags(), *args])
        _mode = mode


def stop():
    """Stop whatever is currently playing."""
    with _lock:
        _stop_locked()


def is_playing_content() -> bool:
    """True while a video/slideshow is actively playing."""
    with _lock:
        return _mode == "content" and _proc is not None and _proc.poll() is None


def content_finished() -> bool:
    """True when content was playing but the mpv process has now exited.

    Used by the playback worker to know when to return to the idle screen.
    """
    with _lock:
        return _mode == "content" and (_proc is None or _proc.poll() is not None)


def show_idle():
    """Display the looping idle/attract image, or a black screen if missing."""
    img = config.IDLE_IMAGE
    if img and os.path.exists(img):
        _start(["--loop-file=inf", "--image-display-duration=inf", img], "idle")
    else:
        logger.info("No idle image at %s — showing a black screen.", img)
        stop()


def play_video(path: str) -> bool:
    """Play a single video file fullscreen. Returns False if the file is missing."""
    full_path = _resolve(path)
    if not os.path.exists(full_path):
        logger.error("Video not found: %s", full_path)
        return False
    _start([full_path], "content")
    return True


def play_slideshow(folder: str, video: str = None) -> bool:
    """Show every photo in a folder as a slideshow, optionally followed by a
    closing video clip. Images and the closing clip are handed to mpv as a
    single playlist, so nothing blocks the caller and there's no flicker
    between the photos and the clip. Returns False if there is nothing to show.
    """
    full_folder = _resolve(folder)
    images = sorted(
        glob.glob(os.path.join(full_folder, "*.jpg"))
        + glob.glob(os.path.join(full_folder, "*.jpeg"))
        + glob.glob(os.path.join(full_folder, "*.png"))
    )
    if not images:
        logger.warning("No images found in %s", full_folder)

    closing = None
    if video:
        candidate = _resolve(video)
        if os.path.exists(candidate):
            closing = candidate
        else:
            logger.warning("Closing video not found: %s", candidate)

    if not images and not closing:
        return False

    args = []
    if images:
        args.append(f"--image-display-duration={config.SLIDESHOW_IMAGE_DURATION}")
        args.extend(images)
    if closing:
        args.append(closing)
    _start(args, "content")
    return True
