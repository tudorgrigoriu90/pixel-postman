"""Safe shutdown / power resilience.

This appliance lives where a child (or a tired parent) will pull the power at
the wall. Unclean shutdowns are the number-one cause of SD-card / storage
corruption on a Raspberry Pi, so we give it a soft power button: hold the
button for a couple of seconds and the Pi shuts down cleanly.

Pair this with a read-only / overlay root filesystem (see README and
scripts/install.sh) for full resilience — that protects against the power
*still* being yanked despite the button.

``gpiozero`` is imported lazily so the rest of the hub (and the test suite)
runs fine on machines without GPIO.
"""
import logging
import subprocess

from . import config

logger = logging.getLogger(__name__)


def default_shutdown():
    """Trigger a clean OS shutdown."""
    logger.info("Power button held — shutting down cleanly.")
    try:
        subprocess.run(["sudo", "shutdown", "-h", "now"], check=False)
    except FileNotFoundError:  # pragma: no cover - platform specific
        logger.error("'shutdown' not found — cannot power off cleanly.")


class PowerButton:
    """Watches a momentary GPIO button and runs a clean shutdown on hold."""

    def __init__(
        self,
        pin=config.POWER_BUTTON_PIN,
        enabled=config.POWER_BUTTON_ENABLED,
        hold_seconds=config.POWER_BUTTON_HOLD_SECONDS,
        on_hold=default_shutdown,
        button=None,
    ):
        self.pin = pin
        self.enabled = enabled
        self.hold_seconds = hold_seconds
        self.on_hold = on_hold
        self._button = button

    def start(self):
        if self._button is not None:
            self._button.when_held = self.on_hold
            return
        if not self.enabled:
            return
        try:
            from gpiozero import Button

            self._button = Button(self.pin, hold_time=self.hold_seconds)
            self._button.when_held = self.on_hold
            logger.info(
                "Power button enabled on GPIO%s (hold %.1fs to shut down).",
                self.pin,
                self.hold_seconds,
            )
        except Exception as exc:  # pragma: no cover - hardware/driver specific
            logger.warning(
                "Power button unavailable (%s); continuing without it.", exc
            )

    def close(self):
        if self._button is not None:
            try:
                self._button.close()
            except Exception:  # pragma: no cover - hardware/driver specific
                pass
