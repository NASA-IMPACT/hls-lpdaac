from __future__ import annotations

import json
from typing import TYPE_CHECKING, Callable

from mypy_boto3_s3.service_resource import Object
from mypy_boto3_sqs.service_resource import Queue

from . import make_sqs_event

if TYPE_CHECKING:
    from aws_lambda_typing.events import SQSEvent


def test_forwards_manifest_from_sqs_event(
    make_s3_object_with_prefix: Callable[[str], Object],
    sqs_queue: Queue,
) -> None:
    # Import here (rather than at top level) to ensure AWS mocks are established.
    # See http://docs.getmoto.org/en/latest/docs/getting_started.html#what-about-those-pesky-imports
    from hls_lpdaac.historical.index import _handler

    s3_object = make_s3_object_with_prefix("L30")
    result = _handler(make_sqs_event(s3_object), queue_url=sqs_queue.url)

    assert result == {"batchItemFailures": []}
    # We expect only 1 message, but we set MaxNumberOfMessages > 1 to allow us
    # to fail the test if there are multiple messages.
    messages = sqs_queue.receive_messages(MaxNumberOfMessages=10)
    assert len(messages) == 1
    assert json.loads(messages[0].body) == json.loads(
        s3_object.get()["Body"].read().decode("utf-8")
    )


def test_forwards_every_message_in_a_batch(
    make_s3_object_with_prefix: Callable[[str], Object],
    sqs_queue: Queue,
) -> None:
    from hls_lpdaac.historical.index import _handler

    first = make_s3_object_with_prefix("L30")
    second = make_s3_object_with_prefix("S30")
    event: "SQSEvent" = {
        "Records": [
            make_sqs_event(first, "m1")["Records"][0],
            make_sqs_event(second, "m2")["Records"][0],
        ]
    }

    result = _handler(event, queue_url=sqs_queue.url)

    assert result == {"batchItemFailures": []}
    assert len(sqs_queue.receive_messages(MaxNumberOfMessages=10)) == 2
