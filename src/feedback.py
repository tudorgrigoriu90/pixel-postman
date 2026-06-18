"""Local LED feedback (a required part of the appliance).

A young child needs to know *immediately* that their scan/tap worked — long
before the TV finishes waking up over HDMI-CEC. A single LED wired to a GPIO
pin provides that confirmation:

    ready / idle      -> off
    scan acknowledged -> a couple of quick blinks
    playing           -> steady on
    error             -> a rapid burst of blinks

The LED is mandatory: if the GPIO library or pin can't be initialized,
``Feedback()`` raises so the hub fails fast rather than running half-blind.
(Individual runtime LED glitches are swallowed so they can never interrupt
playback.) ``gpiozero`` is imported lazily, and a ``led`` can be injected for
unit tests, so this module still imports cleanly off-Pi.
"""
import logging

from . import config

logger = logging.getLogger(__name__)


class Feedback:
    def __init__(self, pin=config.LED_PIN, led=None):
        if led is not None:
            self._led = led
            return
        from gpiozero import LED

        self._led = LED(pin)
        logger.info("LED feedback enabled on GPIO%s", pin)

    def _safe(self, fn):
        try:
            fn()
        except Exception as exc:  # pragma: no cover - hardware/driver specific
            logger.debug("LED operation failed: %s", exc)

    def ready(self):
        """Idle/ready: LED off, waiting for a scan."""
        self._safe(self._led.off)

    def acknowledge(self):
        """A scan/tap was registered — two quick blinks."""
        self._safe(lambda: self._led.blink(on_time=0.08, off_time=0.08, n=2))

    def playing(self):
        """Content is playing — steady on."""
        self._safe(self._led.on)

    def error(self):
        """Unknown code or missing media — a rapid burst of blinks."""
        self._safe(lambda: self._led.blink(on_time=0.06, off_time=0.06, n=6))

    def close(self):
        self._safe(self._led.off)
        self._safe(self._led.close)
