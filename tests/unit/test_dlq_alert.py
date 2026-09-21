from __future__ import annotations

import datetime as dt
import json

import pytest
from mypy_boto3_sqs.service_resource import Queue
from mypy_boto3_ssm import SSMClient

from hls_lpdaac import dlq_alert

WEBHOOK = "https://hooks.slack.example.com/test"
SSM_PATH = "/test/dlq-alert-state"


@pytest.fixture
def posted(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Capture Slack posts instead of making them."""
    messages: list[str] = []
    monkeypatch.setattr(
        dlq_alert, "_post_slack", lambda webhook_url, message: messages.append(message)
    )

    return messages


def run(queue: Queue, alert_interval_hours: int = 12) -> dict:
    return dlq_alert._handler(
        queue_url=queue.url,
        webhook_url=WEBHOOK,
        ssm_path=SSM_PATH,
        stack_name="test-stack",
        alert_interval=dt.timedelta(hours=alert_interval_hours),
    )


def test_no_alert_when_the_dead_letter_queue_is_empty(
    ssm: SSMClient, dead_letter_queue: Queue, posted: list[str]
) -> None:
    result = run(dead_letter_queue)

    assert result == {"depth": 0, "alerted": False}
    assert posted == []


def test_alerts_when_the_dead_letter_queue_is_not_empty(
    ssm: SSMClient, dead_letter_queue: Queue, posted: list[str]
) -> None:
    dead_letter_queue.send_message(MessageBody="stuck")

    result = run(dead_letter_queue)

    assert result == {"depth": 1, "alerted": True}
    assert len(posted) == 1
    assert "test-stack" in posted[0]


def test_repeat_alert_is_throttled(
    ssm: SSMClient, dead_letter_queue: Queue, posted: list[str]
) -> None:
    dead_letter_queue.send_message(MessageBody="stuck")

    run(dead_letter_queue)
    result = run(dead_letter_queue)

    assert result["alerted"] is False
    assert len(posted) == 1


def test_growing_depth_alerts_through_the_throttle(
    ssm: SSMClient, dead_letter_queue: Queue, posted: list[str]
) -> None:
    dead_letter_queue.send_message(MessageBody="stuck")
    run(dead_letter_queue)

    dead_letter_queue.send_message(MessageBody="also stuck")
    result = run(dead_letter_queue)

    assert result == {"depth": 2, "alerted": True}
    assert len(posted) == 2


def test_recovery_alerts_immediately(
    ssm: SSMClient, dead_letter_queue: Queue, posted: list[str]
) -> None:
    dead_letter_queue.send_message(MessageBody="stuck")
    run(dead_letter_queue)

    dead_letter_queue.purge()
    result = run(dead_letter_queue)

    assert result == {"depth": 0, "alerted": True}
    assert len(posted) == 2
    assert "drained" in posted[1]


def test_no_alert_when_the_queue_stays_empty(
    ssm: SSMClient, dead_letter_queue: Queue, posted: list[str]
) -> None:
    run(dead_letter_queue)
    result = run(dead_letter_queue)

    assert result["alerted"] is False
    assert posted == []


def test_state_round_trips_through_ssm(
    ssm: SSMClient, dead_letter_queue: Queue, posted: list[str]
) -> None:
    dead_letter_queue.send_message(MessageBody="stuck")

    run(dead_letter_queue)

    value = ssm.get_parameter(Name=SSM_PATH)["Parameter"].get("Value")
    assert value is not None  # make type checker happy
    stored = json.loads(value)
    assert stored["status"] == "messages"
    assert stored["depth"] == 1


def test_skips_posting_when_no_webhook_is_configured(
    ssm: SSMClient, dead_letter_queue: Queue, posted: list[str]
) -> None:
    dead_letter_queue.send_message(MessageBody="stuck")

    result = dlq_alert._handler(
        queue_url=dead_letter_queue.url,
        webhook_url=None,
        ssm_path=SSM_PATH,
        stack_name="test-stack",
        alert_interval=dt.timedelta(hours=12),
    )

    assert result == {"depth": 1, "alerted": True}
    assert posted == []
