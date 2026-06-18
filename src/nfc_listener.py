"""Reads tag UIDs from a PN532 NFC reader connected over I2C.

This is what powers the postcard project: each postcard has an NFC sticker
on the back; when Antonel sets it on the reader, this thread picks up the
tag's unique ID and hands it off to the dispatcher in main.py.
"""
import logging
import threading
import time

import board
import busio
from adafruit_pn532.i2c import PN532_I2C

from . import config

logger = logging.getLogger(__name__)


class NFCListener(threading.Thread):
    def __init__(self, on_scan, poll_interval=0.5,
                 debounce_seconds=config.NFC_DEBOUNCE_SECONDS):
        super().__init__(daemon=True)
        self.on_scan = on_scan
        self.poll_interval = poll_interval
        self.debounce_seconds = debounce_seconds
        self._last_uid = None
        self._last_time = 0
        self._stop = threading.Event()

    def run(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        pn532 = PN532_I2C(i2c, debug=False)
        pn532.SAM_configuration()
        logger.info("Listening for NFC tags...")

        while not self._stop.is_set():
            uid = pn532.read_passive_target(timeout=0.5)
            if uid:
                uid_hex = "".join(f"{b:02X}" for b in uid)
                now = time.time()
                if uid_hex != self._last_uid or (now - self._last_time) > self.debounce_seconds:
                    logger.info("NFC tag scanned: %s", uid_hex)
                    self.on_scan(uid_hex)
                self._last_uid = uid_hex
                self._last_time = now
            time.sleep(self.poll_interval)

    def stop(self):
        self._stop.set()
