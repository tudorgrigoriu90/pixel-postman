from unittest.mock import MagicMock

import main


def _patch(monkeypatch):
    fake_player = MagicMock()
    fake_tv = MagicMock()
    fake_feedback = MagicMock()
    monkeypatch.setattr(main, "player", fake_player)
    monkeypatch.setattr(main, "tv_control", fake_tv)
    monkeypatch.setattr(main, "feedback", fake_feedback)
    return fake_player, fake_tv, fake_feedback


def test_play_action_dispatches_by_type(monkeypatch):
    fake_player, _, _ = _patch(monkeypatch)
    fake_player.play_video.return_value = True

    assert main.play_action({"type": "video", "path": "a.mp4"}) is True
    fake_player.play_video.assert_called_once_with("a.mp4")

    main.play_action({"type": "slideshow", "folder": "venice", "video": "c.mp4"})
    fake_player.play_slideshow.assert_called_once_with("venice", "c.mp4")


def test_play_action_unknown_type(monkeypatch):
    _patch(monkeypatch)
    assert main.play_action({"type": "bogus"}) is False


def test_process_none_signals_error(monkeypatch):
    _, fake_tv, fake_feedback = _patch(monkeypatch)
    main._process(None)
    fake_feedback.error.assert_called_once()
    fake_tv.ensure_on.assert_not_called()  # no TV wake for an unmapped code


def test_process_success_plays_and_lights_led(monkeypatch):
    fake_player, fake_tv, fake_feedback = _patch(monkeypatch)
    fake_player.play_video.return_value = True

    main._process({"type": "video", "path": "a.mp4"})

    fake_feedback.acknowledge.assert_called_once()
    fake_tv.ensure_on.assert_called_once()
    fake_feedback.playing.assert_called_once()


def test_process_missing_media_falls_back_to_idle(monkeypatch):
    fake_player, _, fake_feedback = _patch(monkeypatch)
    fake_player.play_video.return_value = False

    main._process({"type": "video", "path": "gone.mp4"})

    fake_feedback.error.assert_called_once()
    fake_player.show_idle.assert_called_once()


def test_handlers_enqueue_resolved_action(monkeypatch):
    _patch(monkeypatch)
    monkeypatch.setattr(main.mapper, "resolve_qr", lambda c: {"type": "video", "path": "x"})
    main._play_queue.queue.clear()
    main.handle_qr("BOOK-PAGE-01")
    assert main._play_queue.get_nowait() == {"type": "video", "path": "x"}
