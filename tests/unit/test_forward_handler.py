from __future__ import annotations

import json
from typing import TYPE_CHECKING, Callable

import pytest
from mypy_boto3_s3.service_resource import Bucket, Object
from mypy_boto3_sqs.service_resource import Queue

from . import make_sqs_event

if TYPE_CHECKING:
    from aws_lambda_typing.events import SQSEvent


@pytest.mark.parametrize("prefix", ["L30", "S30", "L30_VI", "S30_VI"])
def test_forwards_manifest_from_sqs_event(
    prefix: str,
    make_s3_object_with_prefix: Callable[[str], Object],
    sqs_queue: Queue,
) -> None:
    # Import here (rather than at top level) to ensure AWS mocks are established.
    # See http://docs.getmoto.org/en/latest/docs/getting_started.html#what-about-those-pesky-imports
    from hls_lpdaac.forward import _handler

    s3_object = make_s3_object_with_prefix(prefix)
    result = _handler(make_sqs_event(s3_object), lpdaac_queue_url=sqs_queue.url)

    assert result == {"batchItemFailures": []}
    messages = sqs_queue.receive_messages(MaxNumberOfMessages=10)
    assert len(messages) == 1
    assert json.loads(messages[0].body) == json.loads(
        s3_object.get()["Body"].read().decode("utf-8")
    )


def test_forwards_every_message_in_a_batch(
    make_s3_object_with_prefix: Callable[[str], Object],
    sqs_queue: Queue,
) -> None:
    from hls_lpdaac.forward import _handler

    first = make_s3_object_with_prefix("L30")
    second = make_s3_object_with_prefix("S30")
    event: "SQSEvent" = {
        "Records": [
            make_sqs_event(first, "m1")["Records"][0],
            make_sqs_event(second, "m2")["Records"][0],
        ]
    }

    result = _handler(event, lpdaac_queue_url=sqs_queue.url)

    assert result == {"batchItemFailures": []}
    messages = sqs_queue.receive_messages(MaxNumberOfMessages=10)
    assert len(messages) == 2


def test_reports_unreadable_object_as_batch_item_failure(
    s3_bucket: Bucket, sqs_queue: Queue
) -> None:
    from hls_lpdaac.forward import _handler

    missing = s3_bucket.Object("L30/does-not-exist.v2.0.json")
    body = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": missing.bucket_name},
                    "object": {"key": missing.key},
                }
            }
        ]
    }
    event: "SQSEvent" = {
        "Records": [
            {
                "messageId": "m1",
                "receiptHandle": "",
                "body": json.dumps(body),
                "attributes": {},
                "messageAttributes": {},
                "md5OfBody": "",
                "eventSource": "aws:sqs",
                "eventSourceARN": "",
                "awsRegion": "us-east-1",
            }
        ]
    }

    result = _handler(event, lpdaac_queue_url=sqs_queue.url)

    assert result == {"batchItemFailures": [{"itemIdentifier": "m1"}]}
    assert sqs_queue.receive_messages(MaxNumberOfMessages=10) == []
