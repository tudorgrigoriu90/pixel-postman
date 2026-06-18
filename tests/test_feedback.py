from unittest.mock import MagicMock

from src.feedback import Feedback


def test_disabled_is_noop():
    fb = Feedback(enabled=False)
    # None of these should raise even though there's no LED.
    fb.ready()
    fb.acknowledge()
    fb.playing()
    fb.error()
    fb.close()


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


def test_led_errors_are_swallowed():
    led = MagicMock()
    led.on.side_effect = RuntimeError("gpio boom")
    fb = Feedback(led=led)
    fb.playing()  # must not raise
