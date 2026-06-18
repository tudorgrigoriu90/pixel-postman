"""Safe shutdown / power resilience (a required part of the appliance).

This appliance lives where a child (or a tired parent) will pull the power at
the wall. Unclean shutdowns are the number-one cause of SD-card / storage
corruption on a Raspberry Pi, so we give it a soft power button: hold the
button for a couple of seconds and the Pi shuts down cleanly.

The button defaults to GPIO26 rather than the "classic" GPIO3 power-button
pin, because GPIO3 doubles as I2C1 SCL and is already used by the PN532 NFC
reader. (Tradeoff: GPIO3 can wake the Pi from halt; GPIO26 cannot, so after a
shutdown you power back on by briefly reconnecting the supply.)

Pair this with a read-only / overlay root filesystem (see README and
scripts/install.sh) for full resilience — that protects against the power
*still* being yanked despite the button.

The power button is mandatory: if the GPIO library or pin can't be
initialized, ``start()`` raises so the hub fails fast. ``gpiozero`` is
imported lazily, and a ``button`` can be injected for unit tests, so this
module still imports cleanly off-Pi.
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
        hold_seconds=config.POWER_BUTTON_HOLD_SECONDS,
        on_hold=default_shutdown,
        button=None,
    ):
        self.pin = pin
        self.hold_seconds = hold_seconds
        self.on_hold = on_hold
        self._button = button

    def start(self):
        if self._button is None:
            from gpiozero import Button

            self._button = Button(self.pin, hold_time=self.hold_seconds)
            logger.info(
                "Power button enabled on GPIO%s (hold %.1fs to shut down).",
                self.pin,
                self.hold_seconds,
            )
        self._button.when_held = self.on_hold

    def close(self):
        if self._button is not None:
            try:
                self._button.close()
            except Exception:  # pragma: no cover - hardware/driver specific
                pass
