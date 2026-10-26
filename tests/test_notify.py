from unittest.mock import patch

import pytest

from src import notify


@pytest.fixture(autouse=True)
def no_retry_delay(monkeypatch):
    monkeypatch.setattr(notify.time, "sleep", lambda seconds: None)


def test_delivered_on_first_attempt():
    users = [{"email": "a@example.com"}]

    with patch.object(notify, "send_email", return_value=True) as send:
        result = notify.bulk_notify(users, "hello")

    assert result["sent"] == 1
    assert result["failed"] == 0
    assert result["failed_emails"] == []
    assert send.call_count == 1


def test_retry_then_success():
    users = [{"email": "a@example.com"}]

    with patch.object(notify, "send_email", side_effect=[Exception("err"), True]) as send:
        result = notify.bulk_notify(users, "hello")

    assert result["sent"] == 1
    assert result["failed"] == 0
    assert result["failed_emails"] == []
    assert send.call_count == 2


def test_gives_up_after_three_attempts():
    users = [{"email": "a@example.com"}]

    with patch.object(notify, "send_email", side_effect=[Exception("err")] * 3) as send:
        result = notify.bulk_notify(users, "hello")

    assert result["sent"] == 0
    assert result["failed"] == 1
    assert result["failed_emails"] == ["a@example.com"]
    assert send.call_count == notify.MAX_ATTEMPTS == 3


def test_failure_is_logged_to_stderr(capsys):
    users = [{"email": "a@example.com"}]

    with patch.object(notify, "send_email", side_effect=[Exception("smtp down")] * 3):
        notify.bulk_notify(users, "hello")

    stderr = capsys.readouterr().err
    assert "[NOTIFY]" in stderr
    assert "smtp down" in stderr
    for attempt in (1, 2, 3):
        assert f"attempt {attempt}/3 failed" in stderr
    assert "giving up after all attempts" in stderr


def test_falsy_return_counts_as_failure():
    users = [{"email": "a@example.com"}]

    with patch.object(notify, "send_email", return_value=False) as send:
        result = notify.bulk_notify(users, "hello")

    assert result["sent"] == 0
    assert result["failed"] == 1
    assert send.call_count == 3


def test_mixed_batch_reports_only_the_broken_address():
    users = [
        {"email": "ok@example.com"},
        {"email": "broken@example.com"},
        {"email": "also-ok@example.com"},
    ]
    first_delivered = [True]
    broken_exhausts_attempts = [Exception("err")] * 3
    last_delivered = [True]
    outcomes = first_delivered + broken_exhausts_attempts + last_delivered

    with patch.object(notify, "send_email", side_effect=outcomes):
        result = notify.bulk_notify(users, "hello")

    assert result["sent"] == 2
    assert result["failed"] == 1
    assert result["failed_emails"] == ["broken@example.com"]


def test_result_keeps_backward_compatible_keys():
    with patch.object(notify, "send_email", return_value=True):
        result = notify.bulk_notify([{"email": "a@example.com"}], "hello")

    assert {"sent", "failed"} <= set(result)
    assert isinstance(result["sent"], int)
    assert isinstance(result["failed"], int)


def test_log_notification_writes_to_stderr(capsys):
    notify.log_notification(42, "bulk", "failed")

    captured = capsys.readouterr()
    assert captured.err.strip() == "[NOTIFY] user=42 type=bulk status=failed"
    assert captured.out == ""
