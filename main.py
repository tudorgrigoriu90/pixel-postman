"""Entry point for PixelPostman.

Runs two listeners in parallel — the QR scanner (for the interactive book) and
the NFC reader (for the travel postcards) — and feeds whatever is scanned to a
single playback worker. The worker serializes everything, so a QR scan and an
NFC tap can never fight over the screen: it acknowledges the scan on the LED,
wakes the TV (only if needed), plays the mapped content, and returns to the
idle screen when playback finishes.
"""
import logging
import queue
import signal
import threading

from src import player, tv_control
from src.content_mapper import ContentMapper
from src.feedback import Feedback
from src.nfc_listener import NFCListener
from src.power import PowerButton
from src.qr_listener import QRListener

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hub")

mapper = ContentMapper()
feedback = Feedback()
_play_queue: "queue.Queue" = queue.Queue()
_stop_event = threading.Event()


def play_action(action: dict) -> bool:
    """Run a single mapped action. Returns True on success."""
    action_type = action.get("type")
    if action_type == "video":
        return player.play_video(action["path"])
    if action_type == "slideshow":
        return player.play_slideshow(action["folder"], action.get("video"))
    logger.warning("Unknown action type in mapping.json: %s", action_type)
    return False


def _process(action):
    """Handle one queued scan result (None means 'no content mapped')."""
    if not action:
        logger.warning("No content mapped for this code/tag — check mapping.json.")
        feedback.error()
        return
    feedback.acknowledge()
    tv_control.ensure_on()
    if play_action(action):
        feedback.playing()
    else:
        feedback.error()
        player.show_idle()
        feedback.ready()


def dispatch(action):
    _play_queue.put(action)


def handle_qr(code: str):
    dispatch(mapper.resolve_qr(code))


def handle_nfc(uid: str):
    dispatch(mapper.resolve_nfc(uid))


def _playback_worker():
    player.show_idle()
    feedback.ready()
    while not _stop_event.is_set():
        try:
            action = _play_queue.get(timeout=0.5)
        except queue.Empty:
            # Nothing waiting: if content just finished, return to idle.
            if player.content_finished():
                player.show_idle()
                feedback.ready()
            continue
        _process(action)


def main():
    worker = threading.Thread(target=_playback_worker, daemon=True)
    qr_thread = QRListener(on_scan=handle_qr)
    nfc_thread = NFCListener(on_scan=handle_nfc)
    power_button = PowerButton()

    worker.start()
    qr_thread.start()
    nfc_thread.start()
    power_button.start()

    def shutdown(*_):
        logger.info("Shutting down.")
        _stop_event.set()
        nfc_thread.stop()
        player.stop()
        feedback.close()
        power_button.close()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    logger.info("Hub running. Waiting for QR scans and NFC taps... (Ctrl+C to stop)")
    _stop_event.wait()


if __name__ == "__main__":
    main()
