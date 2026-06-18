"""Entry point for the PixelPostman.

Runs two listeners in parallel — the QR scanner (for the interactive book)
and the NFC reader (for the travel postcards) — and dispatches whatever is
scanned to the right content on the TV, after waking it via HDMI-CEC.
"""
import logging

from src import tv_control
from src.content_mapper import ContentMapper
from src.nfc_listener import NFCListener
from src.player import play_slideshow, play_video
from src.qr_listener import QRListener

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hub")

mapper = ContentMapper()


def dispatch(action: dict):
    if not action:
        logger.warning("No content mapped for this code/tag — check config/mapping.json.")
        return

    tv_control.power_on_and_select_input()

    action_type = action.get("type")
    if action_type == "video":
        play_video(action["path"])
    elif action_type == "slideshow":
        play_slideshow(action["folder"], action.get("video"))
    else:
        logger.warning("Unknown action type in mapping.json: %s", action_type)


def handle_qr(code: str):
    dispatch(mapper.resolve_qr(code))


def handle_nfc(uid: str):
    dispatch(mapper.resolve_nfc(uid))


def main():
    qr_thread = QRListener(on_scan=handle_qr)
    nfc_thread = NFCListener(on_scan=handle_nfc)

    qr_thread.start()
    nfc_thread.start()

    logger.info("Hub running. Waiting for QR scans and NFC taps... (Ctrl+C to stop)")
    try:
        qr_thread.join()
        nfc_thread.join()
    except KeyboardInterrupt:
        logger.info("Shutting down.")
        nfc_thread.stop()


if __name__ == "__main__":
    main()
