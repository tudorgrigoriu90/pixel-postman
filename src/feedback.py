"""Local LED feedback.

A young child needs to know *immediately* that their scan/tap worked — long
before the TV finishes waking up over HDMI-CEC. A single LED wired to a GPIO
pin provides that confirmation:

    ready / idle      -> off
    scan acknowledged -> a couple of quick blinks
    playing           -> steady on
    error             -> a rapid burst of blinks

The hardware (``gpiozero``) is imported lazily and every call degrades to a
no-op if the LED is disabled or the library/pin is unavailable, so the rest of
the hub runs unchanged on a dev machine or a Pi without the LED fitted.
"""
import logging

from . import config

logger = logging.getLogger(__name__)


class Feedback:
    def __init__(self, pin=config.LED_PIN, enabled=config.LED_ENABLED, led=None):
        self._led = led
        if self._led is None and enabled:
            try:
                from gpiozero import LED

                self._led = LED(pin)
                logger.info("LED feedback enabled on GPIO%s", pin)
            except Exception as exc:  # pragma: no cover - hardware/driver specific
                logger.warning(
                    "LED feedback unavailable (%s); continuing without it.", exc
                )
                self._led = None

    def _safe(self, fn):
        if self._led is None:
            return
        try:
            fn()
        except Exception as exc:  # pragma: no cover - hardware/driver specific
            logger.debug("LED operation failed: %s", exc)

    def ready(self):
        """Idle/ready: LED off, waiting for a scan."""
        self._safe(self._led.off if self._led else (lambda: None))

    def acknowledge(self):
        """A scan/tap was registered — two quick blinks."""
        self._safe(lambda: self._led.blink(on_time=0.08, off_time=0.08, n=2))

    def playing(self):
        """Content is playing — steady on."""
        self._safe(self._led.on if self._led else (lambda: None))

    def error(self):
        """Unknown code or missing media — a rapid burst of blinks."""
        self._safe(lambda: self._led.blink(on_time=0.06, off_time=0.06, n=6))

    def close(self):
        if self._led is not None:
            self._safe(self._led.off)
            self._safe(self._led.close)
