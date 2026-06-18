import pytest

from src import qr_listener

# These tests exercise the pure decoding logic and need evdev's keycode
# constants (available on Linux, including CI).
ecodes = pytest.importorskip(
    "evdev.ecodes", reason="evdev required for QR keymap tests"
)


def _scan(seq):
    """Feed (scancode, shifted) pairs; return the decoded string on Enter."""
    listener = qr_listener.QRListener(on_scan=lambda c: None)
    for scancode, shifted in seq:
        listener._consume(scancode, shifted=shifted)
    return listener._consume(ecodes.KEY_ENTER)


def test_uppercase_code_with_shift():
    seq = [
        (ecodes.KEY_B, True), (ecodes.KEY_O, True), (ecodes.KEY_O, True),
        (ecodes.KEY_K, True), (ecodes.KEY_MINUS, False),
        (ecodes.KEY_0, False), (ecodes.KEY_1, False),
    ]
    assert _scan(seq) == "BOOK-01"


def test_lowercase_default_and_shifted_symbols():
    # A URL-ish payload: lowercase letters by default, '_' and '/' via shift.
    seq = [
        (ecodes.KEY_A, False), (ecodes.KEY_B, False),
        (ecodes.KEY_MINUS, True),   # '_'
        (ecodes.KEY_SLASH, False),  # '/'
        (ecodes.KEY_9, False),
    ]
    assert _scan(seq) == "ab_/9"


def test_enter_with_empty_buffer_returns_none():
    listener = qr_listener.QRListener(on_scan=lambda c: None)
    assert listener._consume(ecodes.KEY_ENTER) is None
