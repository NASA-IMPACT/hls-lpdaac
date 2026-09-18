from __future__ import annotations

import json
from typing import TYPE_CHECKING, Callable

from mypy_boto3_s3.service_resource import Bucket, Object
from mypy_boto3_sqs.service_resource import Queue

from hls_lpdaac.historical.index import PROVIDER, _handler

from . import make_sqs_event
from .conftest import CNM_MANIFEST

if TYPE_CHECKING:
    from aws_lambda_typing.events import SQSEvent


def test_forwards_manifest_from_sqs_event(
    make_s3_object_with_prefix: Callable[[str], Object],
    sqs_queue: Queue,
) -> None:
    s3_object = make_s3_object_with_prefix("L30")
    result = _handler(make_sqs_event(s3_object), queue_url=sqs_queue.url)

    assert result == {"batchItemFailures": []}
    # We expect only 1 message, but we set MaxNumberOfMessages > 1 to allow us
    # to fail the test if there are multiple messages.
    messages = sqs_queue.receive_messages(MaxNumberOfMessages=10)
    assert len(messages) == 1
    expected = {
        **json.loads(s3_object.get()["Body"].read().decode("utf-8")),
        "provider": PROVIDER,
    }
    assert json.loads(messages[0].body) == expected


def test_forwards_every_message_in_a_batch(
    make_s3_object_with_prefix: Callable[[str], Object],
    sqs_queue: Queue,
) -> None:
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


def test_provider_constant_is_exact() -> None:
    assert PROVIDER == "lp_HLS_2.0_BACKWARD_PROCESSED"


def test_injects_the_provider_into_the_forwarded_message(
    make_s3_object_with_prefix: Callable[[str], Object],
    sqs_queue: Queue,
) -> None:
    s3_object = make_s3_object_with_prefix("L30")
    result = _handler(make_sqs_event(s3_object), queue_url=sqs_queue.url)

    assert result == {"batchItemFailures": []}
    messages = sqs_queue.receive_messages(MaxNumberOfMessages=10)
    assert json.loads(messages[0].body)["provider"] == PROVIDER


def test_reports_a_preset_provider_as_a_batch_item_failure(
    s3_bucket: Bucket, sqs_queue: Queue
) -> None:
    s3_object = s3_bucket.put_object(
        Key="L30/preset.v2.0.json",
        Body=json.dumps({**CNM_MANIFEST, "provider": "someone-else"}).encode("utf-8"),
    )

    result = _handler(make_sqs_event(s3_object), queue_url=sqs_queue.url)

    assert result == {"batchItemFailures": [{"itemIdentifier": "m1"}]}
    assert sqs_queue.receive_messages(MaxNumberOfMessages=10) == []
