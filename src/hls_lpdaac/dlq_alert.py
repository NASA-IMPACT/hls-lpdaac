"""Scheduled dead-letter queue depth alerter.

Posts to a Slack incoming webhook when forwarder notifications land in the
dead-letter queue, and again once the queue is drained.

Repeat alerts are throttled, because a dead-letter queue stays non-empty until
someone drains it and an unthrottled check would alert on every run. A depth
that has grown since the last alert is reported through the throttle, since
that means new failures rather than the same backlog.

Environment variables:
  DLQ_URL               - URL of the dead-letter queue to watch
  SLACK_WEBHOOK_URL     - Slack incoming webhook (optional; skips posting if unset)
  ALERT_STATE_SSM_PATH  - SSM parameter path for throttle state
  ALERT_INTERVAL_HOURS  - Min hours between repeated alerts (default: 12)
  STACK_NAME            - Included in the alert text
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import os
import urllib.request
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from botocore.exceptions import ClientError

from hls_lpdaac.aws import sqs_client, ssm_client

if TYPE_CHECKING:  # pragma: no cover
    from aws_lambda_typing.context import Context


@dataclass
class AlertState:
    status: Literal["empty", "messages"] = "empty"
    last_alert_sent: dt.datetime | None = None
    depth: int = 0


def handler(event: dict, _: "Context") -> dict:
    return _handler(  # pragma: no cover
        queue_url=os.environ["DLQ_URL"],
        webhook_url=os.getenv("SLACK_WEBHOOK_URL") or None,
        ssm_path=os.environ["ALERT_STATE_SSM_PATH"],
        stack_name=os.environ["STACK_NAME"],
        alert_interval=dt.timedelta(hours=int(os.getenv("ALERT_INTERVAL_HOURS", "12"))),
    )


# Enables unit testing without the need to monkeypatch `os.environ` (which would
# be necessary to test `handler` above).
def _handler(
    *,
    queue_url: str,
    webhook_url: str | None,
    ssm_path: str,
    stack_name: str,
    alert_interval: dt.timedelta,
) -> dict:
    depth = _depth(queue_url)
    state = _get_state(ssm_path)
    now = dt.datetime.now(tz=dt.timezone.utc)
    alerted = False

    if depth > 0:
        if _alert_due(state, depth, alert_interval):
            message = (
                f":rotating_light: [{stack_name}] {depth} LPDAAC notification(s) "
                f"in the dead-letter queue. Those granules were never announced "
                f"to LPDAAC. Queue: {queue_url}"
            )
            _alert(webhook_url, message)
            alerted = True
            state = AlertState(status="messages", last_alert_sent=now, depth=depth)
        else:
            print(f"Dead-letter queue still holds {depth} message(s); alert throttled.")
            state = AlertState(
                status="messages",
                last_alert_sent=state.last_alert_sent,
                depth=depth,
            )
    else:
        if state.status == "messages":
            message = (
                f":white_check_mark: [{stack_name}] The LPDAAC notification "
                f"dead-letter queue has been drained."
            )
            _alert(webhook_url, message)
            alerted = True
        else:
            print("Dead-letter queue is empty. No alert needed.")
        state = AlertState(status="empty", last_alert_sent=now, depth=0)

    _put_state(ssm_path, state)

    return {"depth": depth, "alerted": alerted}


def _depth(queue_url: str) -> int:
    """Return the approximate number of messages in the queue."""
    region_name = queue_url.split(".")[1]
    attributes = sqs_client(region_name).get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=["ApproximateNumberOfMessages"],
    )["Attributes"]

    return int(attributes["ApproximateNumberOfMessages"])


def _alert_due(state: AlertState, depth: int, alert_interval: dt.timedelta) -> bool:
    """Return True if this depth warrants a Slack post."""
    if state.last_alert_sent is None:
        return True
    if depth > state.depth:
        return True

    return dt.datetime.now(tz=dt.timezone.utc) - state.last_alert_sent >= alert_interval


def _alert(webhook_url: str | None, message: str) -> None:
    print(message)
    if webhook_url:
        _post_slack(webhook_url, message)


def _post_slack(webhook_url: str, message: str) -> None:
    """Send a plain text message to a Slack incoming webhook."""
    payload = json.dumps({"text": message}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        print(f"Slack response: {resp.status}")


def _get_state(ssm_path: str) -> AlertState:
    """Read alert state from SSM, defaulting when the parameter does not exist."""
    try:
        response = ssm_client().get_parameter(Name=ssm_path, WithDecryption=False)
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "ParameterNotFound":
            return AlertState()
        raise

    value = response.get("Parameter", {}).get("Value")
    if not value:
        return AlertState()

    data = json.loads(value)
    if data.get("last_alert_sent"):
        data["last_alert_sent"] = dt.datetime.fromisoformat(data["last_alert_sent"])

    return AlertState(**data)


def _put_state(ssm_path: str, state: AlertState) -> None:
    """Persist alert state to SSM."""

    def serialize(obj: object) -> str:
        if isinstance(obj, dt.datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    ssm_client().put_parameter(
        Name=ssm_path,
        Value=json.dumps(dataclasses.asdict(state), default=serialize),
        Type="String",
        Overwrite=True,
    )
