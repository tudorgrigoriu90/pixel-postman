from src import selftest


def test_selftest_runs_without_hardware_and_reports_failure(capsys):
    # Off-Pi (no GPIO, no PN532, no scanner device) the self-test must still
    # complete cleanly, print a report, and return a boolean.
    result = selftest.run_selftest()
    assert result is False  # required hardware is absent on the CI runner

    out = capsys.readouterr().out
    assert "PixelPostman self-test" in out
    assert "Feedback LED" in out
    assert "NFC reader (PN532)" in out


def test_check_isolates_failures(capsys):
    name, ok = selftest._check("Boom", lambda: (_ for _ in ()).throw(RuntimeError("x")))
    assert (name, ok) == ("Boom", False)
    assert "[FAIL] Boom" in capsys.readouterr().out
