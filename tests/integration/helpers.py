from __future__ import annotations

import time

from mypy_boto3_sqs.service_resource import Queue
from mypy_boto3_ssm import SSMClient

# The path under test is S3 -> SQS -> Lambda -> destination queue, and these
# tests run against a stack deployed moments earlier, so they race a freshly
# created event source mapping, which can take about a minute to begin polling.
DELIVERY_TIMEOUT_SECONDS = 180.0

# Long enough for SQS to answer from every host holding a copy of the queue,
# short enough that asserting "nothing else arrived" stays cheap.
DRAIN_WAIT_SECONDS = 5


def ssm_param_value(ssm: SSMClient, name: str) -> str:
    value = ssm.get_parameter(Name=name)["Parameter"].get("Value")
    assert value is not None  # make type checker happy

    return value


def fetch_messages(
    queue: Queue,
    *,
    expected: int,
    timeout: float = DELIVERY_TIMEOUT_SECONDS,
) -> list[str]:
    """Return the bodies of `expected` messages, waiting up to `timeout`.

    Returns early once `expected` messages have arrived, and returns whatever
    arrived if the deadline passes first, so the caller's assertion reports the
    shortfall rather than a timeout.

    Received messages are deleted, so a caller that wants to prove nothing
    further arrived can follow up with `remaining_messages`.
    """
    deadline = time.monotonic() + timeout
    bodies: list[str] = []

    while len(bodies) < expected:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break

        messages = queue.receive_messages(
            MaxNumberOfMessages=10,
            WaitTimeSeconds=max(1, min(20, int(remaining))),
        )
        if not messages:
            continue

        queue.delete_messages(
            Entries=[
                {"Id": message.message_id, "ReceiptHandle": message.receipt_handle}
                for message in messages
            ]
        )
        bodies.extend(message.body for message in messages)

    return bodies


def remaining_messages(queue: Queue) -> list[str]:
    """Return anything still on the queue, to catch duplicate deliveries."""
    messages = queue.receive_messages(
        MaxNumberOfMessages=10, WaitTimeSeconds=DRAIN_WAIT_SECONDS
    )

    return [message.body for message in messages]
