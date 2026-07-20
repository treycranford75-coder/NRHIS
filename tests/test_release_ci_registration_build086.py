from pathlib import Path

SCRIPT = Path("scripts/release/Finish-NrhisBuildLifecycle.ps1")


def _text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_no_checks_is_treated_as_pending_with_retries() -> None:
    text = _text()
    assert "$checkRegistrationAttempts = 12" in text
    assert "$checkRegistrationDelaySeconds = 10" in text
    assert "no checks reported" in text
    assert "Start-Sleep -Seconds $checkRegistrationDelaySeconds" in text
    assert "CI checks have not registered" in text


def test_real_ci_failures_remain_blocking() -> None:
    text = _text()
    assert "gh pr checks $PullRequestUrl --watch --fail-fast" in text
    assert "One or more required CI checks failed." in text
    assert "CI failed. Automatic merge blocked." in text


def test_lifecycle_records_pending_and_failed_states() -> None:
    text = _text()
    assert "-Status 'pending'" in text
    assert "-Status 'failed'" in text
