from unittest.mock import MagicMock

from src import power
from src.power import PowerButton


def test_default_shutdown_invokes_shutdown(monkeypatch):
    calls = []
    monkeypatch.setattr(power.subprocess, "run", lambda *a, **k: calls.append(a[0]))
    power.default_shutdown()
    assert calls == [["sudo", "shutdown", "-h", "now"]]


def test_injected_button_wires_hold_handler():
    button = MagicMock()
    handler = MagicMock()
    pb = PowerButton(on_hold=handler, button=button)
    pb.start()
    assert button.when_held is handler


def test_disabled_without_button_is_noop():
    pb = PowerButton(enabled=False)
    pb.start()   # no hardware, must not raise
    pb.close()
