import json
import os
import time

from src.content_mapper import ContentMapper


def _write(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def test_resolve_qr_and_nfc(tmp_path):
    mapping = tmp_path / "mapping.json"
    _write(mapping, {
        "qr": {"BOOK-PAGE-01": {"type": "video", "path": "a.mp4"}},
        "nfc": {"04A3B2C1D2E380": {"type": "slideshow", "folder": "venice"}},
    })
    m = ContentMapper(str(mapping))

    assert m.resolve_qr("BOOK-PAGE-01") == {"type": "video", "path": "a.mp4"}
    assert m.resolve_qr("UNKNOWN") is None
    # NFC UIDs are matched case-insensitively (stored uppercase).
    assert m.resolve_nfc("04a3b2c1d2e380")["folder"] == "venice"
    assert m.resolve_nfc("DEADBEEF") is None


def test_missing_file_is_safe(tmp_path):
    m = ContentMapper(str(tmp_path / "nope.json"))
    assert m.resolve_qr("anything") is None


def test_invalid_json_is_safe(tmp_path):
    mapping = tmp_path / "mapping.json"
    mapping.write_text("{ not valid json", encoding="utf-8")
    m = ContentMapper(str(mapping))
    assert m.resolve_qr("anything") is None


def test_auto_reload_on_change(tmp_path):
    mapping = tmp_path / "mapping.json"
    _write(mapping, {"qr": {"A": {"type": "video", "path": "a.mp4"}}, "nfc": {}})
    m = ContentMapper(str(mapping))
    assert m.resolve_qr("A")["path"] == "a.mp4"

    # Edit the file; bump mtime to be safe on coarse-grained filesystems.
    _write(mapping, {"qr": {"A": {"type": "video", "path": "b.mp4"}}, "nfc": {}})
    os.utime(mapping, (time.time() + 10, time.time() + 10))

    assert m.resolve_qr("A")["path"] == "b.mp4"
