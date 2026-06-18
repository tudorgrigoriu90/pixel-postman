"""Centralized configuration and paths for the PixelPostman."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(BASE_DIR, "content")
MAPPING_FILE = os.path.join(BASE_DIR, "config", "mapping.json")

# QR scanner: path to the HID input device.
# Find the right value by plugging in the scanner and running:
#   ls /dev/input/by-id/
QR_SCANNER_DEVICE = os.environ.get(
    "QR_SCANNER_DEVICE", "/dev/input/by-id/usb-Scanner-event-kbd"
)

# NFC reader connection type. PN532 supports i2c, spi, or uart;
# i2c is the simplest wiring on a Raspberry Pi (4 wires: VCC, GND, SDA, SCL).
NFC_CONNECTION = "i2c"

# Player
MPV_BINARY = "mpv"
SLIDESHOW_IMAGE_DURATION = 4  # seconds each photo is shown in a slideshow

# Debounce: ignore repeated scans of the *same* NFC tag within this window,
# so holding a postcard near the reader doesn't restart playback in a loop.
NFC_DEBOUNCE_SECONDS = 3
