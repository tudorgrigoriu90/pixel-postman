"""HDMI-CEC helpers to wake the TV and switch it to the Pi's input
automatically, so nobody has to touch a remote control.

Requires cec-utils (sudo apt install cec-utils). Most modern TVs
(Samsung/LG/Sony, etc.) support CEC; if a TV doesn't respond reliably,
fall back to a smart plug + IR blaster instead (see README).
"""
import logging
import subprocess

logger = logging.getLogger(__name__)


def power_on_and_select_input():
    """Send CEC commands to wake the TV and make this device the active source."""
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
