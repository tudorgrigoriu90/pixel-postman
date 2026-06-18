import pytest

from src import player


class FakeProc:
    def __init__(self, args):
        self.args = args
        self._poll = None  # None == still running

    def poll(self):
        return self._poll

    def terminate(self):
        self._poll = 0

    def wait(self, timeout=None):
        self._poll = 0
        return 0

    def kill(self):
        self._poll = -9


@pytest.fixture
def fake_mpv(monkeypatch):
    launched = []

    def fake_popen(args):
        proc = FakeProc(args)
        launched.append(proc)
        return proc

    monkeypatch.setattr(player.subprocess, "Popen", fake_popen)
    # Start each test from a clean playback state.
    player._proc = None
    player._mode = None
    return launched


def test_play_video_missing_returns_false(fake_mpv, monkeypatch):
    monkeypatch.setattr(player.os.path, "exists", lambda p: False)
    assert player.play_video("missing.mp4") is False
    assert fake_mpv == []


def test_play_video_launches_mpv_with_vo_flags(fake_mpv, monkeypatch):
    monkeypatch.setattr(player.os.path, "exists", lambda p: True)
    assert player.play_video("stories/a.mp4") is True
    args = fake_mpv[-1].args
    assert player.config.MPV_BINARY == args[0]
    assert "--fullscreen" in args
    assert any(a.startswith("--vo=") for a in args)
    assert args[-1].endswith("stories/a.mp4")
    assert player.is_playing_content() is True


def test_play_slideshow_builds_playlist(fake_mpv, monkeypatch):
    monkeypatch.setattr(player.glob, "glob", lambda pat: ["/c/2.jpg", "/c/1.jpg"]
                        if pat.endswith("*.jpg") else [])
    monkeypatch.setattr(player.os.path, "exists", lambda p: True)

    assert player.play_slideshow("trips/venice", "trips/venice/clip.mp4") is True
    args = fake_mpv[-1].args
    # Images are sorted, duration flag present, closing clip appended last.
    assert any(a.startswith("--image-display-duration=") for a in args)
    assert args.index("/c/1.jpg") < args.index("/c/2.jpg")
    assert args[-1].endswith("clip.mp4")


def test_play_slideshow_no_media_returns_false(fake_mpv, monkeypatch):
    monkeypatch.setattr(player.glob, "glob", lambda pat: [])
    assert player.play_slideshow("trips/empty") is False


def test_starting_new_content_stops_previous(fake_mpv, monkeypatch):
    monkeypatch.setattr(player.os.path, "exists", lambda p: True)
    player.play_video("a.mp4")
    first = fake_mpv[-1]
    player.play_video("b.mp4")
    assert first.poll() is not None  # previous process was terminated


def test_content_finished_transitions(fake_mpv, monkeypatch):
    monkeypatch.setattr(player.os.path, "exists", lambda p: True)
    player.play_video("a.mp4")
    assert player.content_finished() is False
    fake_mpv[-1]._poll = 0  # mpv exited on its own
    assert player.content_finished() is True


def test_show_idle_with_image_loops(fake_mpv, monkeypatch):
    monkeypatch.setattr(player.os.path, "exists", lambda p: True)
    monkeypatch.setattr(player.config, "IDLE_IMAGE", "/c/idle.png")
    player.show_idle()
    args = fake_mpv[-1].args
    assert "--loop-file=inf" in args
    assert player._mode == "idle"


def test_show_idle_without_image_is_black(fake_mpv, monkeypatch):
    monkeypatch.setattr(player.os.path, "exists", lambda p: False)
    player.show_idle()
    assert fake_mpv == []  # nothing launched -> black screen
