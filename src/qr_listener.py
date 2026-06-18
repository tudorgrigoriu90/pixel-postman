"""Reads QR codes from a USB/Bluetooth HID barcode scanner.

These scanners behave like a keyboard: they "type" the encoded text and press
Enter. Reading the raw device file (instead of relying on whatever window has
keyboard focus) means the hub works headless/kiosk-style, with no terminal or
desktop needed.

evdev is imported defensively so this module can be imported (and unit-tested)
on machines without it; the listener only needs it when actually run.
"""
import logging
import threading

try:
    from evdev import InputDevice, categorize, ecodes
except ImportError:  # pragma: no cover - exercised only off-Linux
    InputDevice = categorize = ecodes = None

from . import config

logger = logging.getLogger(__name__)


def _build_keymaps():
    """Return (base, shifted) maps from evdev keycodes to characters."""
    if ecodes is None:  # pragma: no cover - exercised only off-Linux
        return {}, {}

    base = {
        ecodes.KEY_0: "0", ecodes.KEY_1: "1", ecodes.KEY_2: "2", ecodes.KEY_3: "3",
        ecodes.KEY_4: "4", ecodes.KEY_5: "5", ecodes.KEY_6: "6", ecodes.KEY_7: "7",
        ecodes.KEY_8: "8", ecodes.KEY_9: "9",
        ecodes.KEY_MINUS: "-", ecodes.KEY_EQUAL: "=", ecodes.KEY_SLASH: "/",
        ecodes.KEY_DOT: ".", ecodes.KEY_COMMA: ",", ecodes.KEY_SEMICOLON: ";",
        ecodes.KEY_APOSTROPHE: "'", ecodes.KEY_SPACE: " ",
    }
    # Letters: lowercase by default, uppercase when Shift is held.
    shifted = {}
    for letter in "abcdefghijklmnopqrstuvwxyz":
        keycode = getattr(ecodes, f"KEY_{letter.upper()}")
        base[keycode] = letter
        shifted[keycode] = letter.upper()
    # A handful of common shifted symbols seen in QR payloads / URLs.
    shifted.update({
        ecodes.KEY_MINUS: "_", ecodes.KEY_EQUAL: "+", ecodes.KEY_SLASH: "?",
        ecodes.KEY_SEMICOLON: ":", ecodes.KEY_DOT: ">", ecodes.KEY_COMMA: "<",
        ecodes.KEY_2: "@", ecodes.KEY_3: "#", ecodes.KEY_4: "$", ecodes.KEY_5: "%",
    })
    return base, shifted


_KEYMAP, _SHIFT_KEYMAP = _build_keymaps()
_SHIFT_KEYS = (
    {ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT} if ecodes is not None else set()
)


class QRListener(threading.Thread):
    def __init__(self, on_scan, device_path=config.QR_SCANNER_DEVICE):
        super().__init__(daemon=True)
        self.on_scan = on_scan
        self.device_path = device_path
        self._buffer = ""
        self._shift = False

    def _consume(self, scancode, shifted=False):
        """Feed one key-down scancode through the decoder.

        Returns the completed code on Enter, otherwise None. Kept free of any
        evdev I/O so it can be unit-tested directly.
        """
        if scancode == ecodes.KEY_ENTER:
            code, self._buffer = self._buffer, ""
            return code or None
        char = (_SHIFT_KEYMAP if shifted else _KEYMAP).get(scancode)
        if char is not None:
            self._buffer += char
        return None

    def run(self):
        if InputDevice is None:  # pragma: no cover - exercised only off-Linux
            logger.error("evdev not available — QR scanning disabled.")
            return
        try:
            device = InputDevice(self.device_path)
            device.grab()  # keep keystrokes out of any console/login prompt
        except (FileNotFoundError, PermissionError, OSError) as exc:
            logger.error(
                "QR scanner not available at %s (%s). Run 'ls /dev/input/by-id/' "
                "with the scanner plugged in to find the correct path, set "
                "QR_SCANNER_DEVICE, and make sure the service user is in the "
                "'input' group.",
                self.device_path,
                exc,
            )
            return

        logger.info("Listening for QR scans on %s", self.device_path)
        for event in device.read_loop():
            if event.type != ecodes.EV_KEY:
                continue
            key_event = categorize(event)
            # Track shift on key *up* too, so a held shift releases correctly.
            if key_event.scancode in _SHIFT_KEYS:
                self._shift = key_event.keystate == key_event.key_down
                continue
            if key_event.keystate != key_event.key_down:
                continue
            code = self._consume(key_event.scancode, shifted=self._shift)
            if code:
                logger.info("QR scanned: %s", code)
                self.on_scan(code)
