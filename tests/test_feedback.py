from unittest.mock import MagicMock

import pytest

from src.feedback import Feedback


def test_states_drive_the_led():
    led = MagicMock()
    fb = Feedback(led=led)

    fb.playing()
    led.on.assert_called_once()

    fb.ready()
    led.off.assert_called_once()

    fb.acknowledge()
    assert led.blink.called

    led.blink.reset_mock()
    fb.error()
    led.blink.assert_called_once()


def test_led_runtime_errors_are_swallowed():
    led = MagicMock()
    led.on.side_effect = RuntimeError("gpio boom")
    fb = Feedback(led=led)
    fb.playing()  # a runtime glitch must never interrupt playback


def test_missing_hardware_raises():
    # The LED is mandatory: with no injected LED and no usable GPIO backend,
    # construction must fail loudly rather than silently no-op.
    with pytest.raises(Exception):
        Feedback()
