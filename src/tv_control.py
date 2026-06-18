"""HDMI-CEC helpers to wake the TV and switch it to the Pi's input
automatically, so nobody has to touch a remote control.

Requires cec-utils (sudo apt install cec-utils). Most modern TVs
(Samsung/LG/Sony, etc.) support CEC; if a TV doesn't respond reliably,
fall back to a smart plug + IR blaster instead (see README).

The CEC commands are slow and occasionally flaky, so we (a) run them in a
background thread so playback is never gated on them, and (b) avoid re-sending
them on every scan — only if we haven't sent them within CEC_RESEND_SECONDS.
"""
import logging
import subprocess
import threading
import time

from . import config

logger = logging.getLogger(__name__)

_last_sent = 0.0
_lock = threading.Lock()


def _send():
    """Send CEC commands to wake the TV and become the active source."""
    try:
        subprocess.run(
            ["cec-client", "-s", "-d", "1"],
            input="on 0\nas\n",
            text=True,
            timeout=10,
            check=False,
        )
        logger.info("Sent CEC power-on + active-source commands.")
    except FileNotFoundError:
        logger.error("cec-client not found — install with: sudo apt install cec-utils")
    except subprocess.TimeoutExpired:
        logger.warning("CEC command timed out — TV may not support CEC reliably.")


def _send_async():
    threading.Thread(target=_send, daemon=True).start()


def ensure_on(now=None) -> bool:
    """Wake the TV / select this input, unless we did so very recently.

    Returns True if the command was (re)sent, False if skipped as redundant.
    Runs the actual CEC command in the background so the caller isn't blocked.
    """
    global _last_sent
    now = time.time() if now is None else now
    with _lock:
        if now - _last_sent < config.CEC_RESEND_SECONDS:
            return False
        _last_sent = now
    _send_async()
    return True


# Backwards-compatible alias.
def power_on_and_select_input():
    ensure_on()
