"""On-Pi bring-up self-test.

Run ``python main.py --selftest`` after wiring everything up. It probes each
subsystem independently and prints a PASS/FAIL report, so you can tell at a
glance what's working and what still needs attention — without having to scan
a real card and stare at the TV.

Every probe is isolated: one failing component never stops the others from
being checked.
"""
import os
import shutil
import time

from . import config
from .content_mapper import ContentMapper

# Components that must work for the hub to be usable. Others (e.g. the idle
# image) are reported but treated as non-fatal.
_REQUIRED = {
    "Content mapping", "mpv player", "HDMI-CEC (cec-client)",
    "QR scanner device", "Feedback LED", "Power button", "NFC reader (PN532)",
}


def _check(name, fn):
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001 - we want to report any failure
        ok, detail = False, f"{type(exc).__name__}: {exc}"
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    return name, ok


def _mapping():
    m = ContentMapper()
    qr = len(m._mapping.get("qr", {}))
    nfc = len(m._mapping.get("nfc", {}))
    return (qr + nfc) > 0, f"{qr} QR codes, {nfc} NFC tags loaded"


def _idle_image():
    if os.path.exists(config.IDLE_IMAGE):
        return True, f"present ({config.IDLE_IMAGE})"
    return True, f"missing ({config.IDLE_IMAGE}) — idle screen will be black"


def _mpv():
    path = shutil.which(config.MPV_BINARY)
    return bool(path), path or "not found — 'sudo apt install mpv'"


def _cec():
    path = shutil.which("cec-client")
    return bool(path), path or "not found — 'sudo apt install cec-utils'"


def _qr_device():
    exists = os.path.exists(config.QR_SCANNER_DEVICE)
    return exists, (
        config.QR_SCANNER_DEVICE if exists
        else f"{config.QR_SCANNER_DEVICE} not found — set QR_SCANNER_DEVICE"
    )


def _led():
    from .feedback import Feedback

    fb = Feedback()
    for _ in range(3):
        fb.acknowledge()
        time.sleep(0.3)
    fb.playing()
    time.sleep(0.4)
    fb.ready()
    fb.close()
    return True, f"blinked on GPIO{config.LED_PIN} — confirm you saw it flash"


def _power_button():
    from gpiozero import Button

    button = Button(config.POWER_BUTTON_PIN, hold_time=config.POWER_BUTTON_HOLD_SECONDS)
    state = "pressed" if button.is_pressed else "released"
    button.close()
    return True, f"ready on GPIO{config.POWER_BUTTON_PIN} (currently {state})"


def _nfc():
    import board
    import busio
    from adafruit_pn532.i2c import PN532_I2C

    i2c = busio.I2C(board.SCL, board.SDA)
    pn532 = PN532_I2C(i2c, debug=False)
    _ic, ver, rev, _support = pn532.firmware_version
    return True, f"PN532 detected, firmware {ver}.{rev}"


def run_selftest() -> bool:
    print("PixelPostman self-test")
    print("=" * 48)
    results = [
        _check("Content mapping", _mapping),
        _check("Idle image", _idle_image),
        _check("mpv player", _mpv),
        _check("HDMI-CEC (cec-client)", _cec),
        _check("QR scanner device", _qr_device),
        _check("Feedback LED", _led),
        _check("Power button", _power_button),
        _check("NFC reader (PN532)", _nfc),
    ]
    print("=" * 48)
    failed_required = [name for name, ok in results if not ok and name in _REQUIRED]
    if failed_required:
        print("Self-test FAILED — needs attention: " + ", ".join(failed_required))
        return False
    print("Self-test PASSED — the hub is ready to go.")
    return True
