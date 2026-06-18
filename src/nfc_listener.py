"""Reads tag UIDs from a PN532 NFC reader connected over I2C.

This powers the postcard project: each postcard has an NFC sticker on the
back; when it's set on the reader, this thread picks up the tag's unique ID
and hands it off to the dispatcher in main.py.

A tag only fires once per presentation: leaving a postcard resting on the
reader will not re-trigger playback in a loop. Lifting it off and setting it
back down (or swapping in a different postcard) registers as a new scan.

The hardware libraries (board / busio / adafruit_pn532) are imported lazily
inside run(), so this module imports cleanly on a dev machine for testing.
"""
import logging
import threading
import time

from . import config

logger = logging.getLogger(__name__)


class NFCListener(threading.Thread):
    def __init__(self, on_scan, poll_interval=config.NFC_POLL_INTERVAL):
        super().__init__(daemon=True)
        self.on_scan = on_scan
        self.poll_interval = poll_interval
        self._present_uid = None
        self._stop = threading.Event()

    def _decide(self, uid_hex):
        """Given the current reading (a UID hex string, or None if the reader
        is empty), return the UID to fire on, or None.

        Fires only when a tag first appears or a different tag replaces it —
        never repeatedly while the same tag rests on the reader. Pure logic,
        unit-tested directly.
        """
        if uid_hex is None:
            self._present_uid = None
            return None
        if uid_hex == self._present_uid:
            return None
        self._present_uid = uid_hex
        return uid_hex

    def run(self):
        try:
            import board
            import busio
            from adafruit_pn532.i2c import PN532_I2C

            i2c = busio.I2C(board.SCL, board.SDA)
            pn532 = PN532_I2C(i2c, debug=False)
            pn532.SAM_configuration()
        except Exception as exc:  # pragma: no cover - hardware/driver specific
            logger.error(
                "NFC reader not available (%s). Check the PN532 wiring and that "
                "I2C is enabled and the service user is in the 'i2c' group.",
                exc,
            )
            return

        logger.info("Listening for NFC tags...")
        while not self._stop.is_set():
            uid = pn532.read_passive_target(timeout=0.5)
            uid_hex = "".join(f"{b:02X}" for b in uid) if uid else None
            fire = self._decide(uid_hex)
            if fire:
                logger.info("NFC tag scanned: %s", fire)
                self.on_scan(fire)
            time.sleep(self.poll_interval)

    def stop(self):
        self._stop.set()
