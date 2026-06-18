"""Reads QR codes from a USB/Bluetooth HID barcode scanner.

These scanners behave like a keyboard: they "type" the encoded text and
press Enter. Reading the raw device file (instead of relying on whatever
window has keyboard focus) means the hub works headless/kiosk-style,
with no terminal or desktop needed.
"""
import logging
import threading

from evdev import InputDevice, categorize, ecodes

from . import config

logger = logging.getLogger(__name__)

# Map evdev keycodes to characters. Covers digits, letters and a few common
# symbols — enough for typical QR payloads (IDs, short codes, URLs).
_KEYMAP = {
    ecodes.KEY_0: "0", ecodes.KEY_1: "1", ecodes.KEY_2: "2", ecodes.KEY_3: "3",
    ecodes.KEY_4: "4", ecodes.KEY_5: "5", ecodes.KEY_6: "6", ecodes.KEY_7: "7",
    ecodes.KEY_8: "8", ecodes.KEY_9: "9",
    ecodes.KEY_MINUS: "-", ecodes.KEY_SLASH: "/", ecodes.KEY_DOT: ".",
    ecodes.KEY_COLON: ":",
}
for _i, _letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    _KEYMAP[getattr(ecodes, f"KEY_{_letter}")] = _letter


class QRListener(threading.Thread):
    def __init__(self, on_scan, device_path=config.QR_SCANNER_DEVICE):
        super().__init__(daemon=True)
        self.on_scan = on_scan
        self.device_path = device_path
        self._buffer = ""

    def run(self):
        try:
            device = InputDevice(self.device_path)
        except FileNotFoundError:
            logger.error(
                "QR scanner not found at %s. Run 'ls /dev/input/by-id/' "
                "with the scanner plugged in to find the correct path, then "
                "set QR_SCANNER_DEVICE accordingly.",
                self.device_path,
            )
            return

        logger.info("Listening for QR scans on %s", self.device_path)
        for event in device.read_loop():
            if event.type != ecodes.EV_KEY:
                continue
            key_event = categorize(event)
            if key_event.keystate != key_event.key_down:
                continue

            code = key_event.scancode
            if code == ecodes.KEY_ENTER:
                if self._buffer:
                    logger.info("QR scanned: %s", self._buffer)
                    self.on_scan(self._buffer)
                self._buffer = ""
            elif code in _KEYMAP:
                self._buffer += _KEYMAP[code]
