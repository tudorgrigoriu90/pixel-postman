from src import tv_control


def test_ensure_on_dedupes_within_window(monkeypatch):
    calls = []
    monkeypatch.setattr(tv_control, "_send_async", lambda: calls.append(1))
    monkeypatch.setattr(tv_control.config, "CEC_RESEND_SECONDS", 30)
    tv_control._last_sent = 0.0

    assert tv_control.ensure_on(now=1000) is True       # first send
    assert tv_control.ensure_on(now=1005) is False      # too soon, skipped
    assert tv_control.ensure_on(now=1040) is True        # window elapsed, resent
    assert len(calls) == 2
