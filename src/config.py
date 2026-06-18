"""Centralized configuration and paths for PixelPostman.

Every value here can be overridden with an environment variable so the same
code can run on a developer's laptop (for tests) and on the Raspberry Pi
without editing source.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.environ.get("CONTENT_DIR", os.path.join(BASE_DIR, "content"))
MAPPING_FILE = os.environ.get(
    "MAPPING_FILE", os.path.join(BASE_DIR, "config", "mapping.json")
)

# QR scanner: path to the HID input device.
# Find the right value by plugging in the scanner and running:
#   ls /dev/input/by-id/
QR_SCANNER_DEVICE = os.environ.get(
    "QR_SCANNER_DEVICE", "/dev/input/by-id/usb-Scanner-event-kbd"
)

# NFC reader connection type. PN532 supports i2c, spi, or uart;
# i2c is the simplest wiring on a Raspberry Pi (4 wires: VCC, GND, SDA, SCL).
NFC_CONNECTION = os.environ.get("NFC_CONNECTION", "i2c")
NFC_POLL_INTERVAL = float(os.environ.get("NFC_POLL_INTERVAL", "0.3"))

# Player
MPV_BINARY = os.environ.get("MPV_BINARY", "mpv")
SLIDESHOW_IMAGE_DURATION = int(os.environ.get("SLIDESHOW_IMAGE_DURATION", "4"))
# On Raspberry Pi OS Lite there is no desktop/compositor, so mpv must render
# straight to the framebuffer via DRM/KMS. These defaults make fullscreen
# playback work on a headless Pi; set MPV_GPU_CONTEXT="" to let mpv decide
# (useful when running under a desktop or on a dev machine).
MPV_VIDEO_OUTPUT = os.environ.get("MPV_VIDEO_OUTPUT", "gpu")
MPV_GPU_CONTEXT = os.environ.get("MPV_GPU_CONTEXT", "drm")

# Idle / attract screen shown whenever nothing is playing, so the child never
# sees a Linux console. Drop any image here; if it is missing the screen just
# goes black instead.
IDLE_IMAGE = os.environ.get("IDLE_IMAGE", os.path.join(CONTENT_DIR, "idle.png"))

# HDMI-CEC: don't re-send the (slow, sometimes flaky) power-on/active-source
# commands on every single scan — only if we haven't sent them recently.
CEC_RESEND_SECONDS = int(os.environ.get("CEC_RESEND_SECONDS", "30"))

# --- Local feedback LED (required hardware) ------------------------------
# A single LED wired to a GPIO pin gives the child instant confirmation that
# a scan/tap registered, even before the TV wakes up. This is a core part of
# the appliance: if it can't be initialized the hub refuses to start. Only
# the pin (BCM numbering) is configurable.
LED_PIN = int(os.environ.get("LED_PIN", "17"))

# --- Safe shutdown / power resilience (required hardware) ----------------
# A momentary push button wired between this GPIO and ground. Holding it
# triggers a clean shutdown so the SD card / storage isn't corrupted by
# yanking power. GPIO3 is special on the Pi: a press can also wake the board
# back up from halt, making it a natural soft power button. Also a core part
# of the appliance — the hub refuses to start if it can't be initialized.
POWER_BUTTON_PIN = int(os.environ.get("POWER_BUTTON_PIN", "3"))
POWER_BUTTON_HOLD_SECONDS = float(os.environ.get("POWER_BUTTON_HOLD_SECONDS", "2"))
