from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aws_lambda_typing.events import S3Event
    from mypy_boto3_s3.service_resource import Object
    from mypy_boto3_sqs.service_resource import Queue


def test_lpdaac_historical_handler(
    s3_event: S3Event,
    s3_object: Object,
    sqs_queue: Queue,
) -> None:
    # Import here (rather than at top level) to ensure AWS mocks are established.
    # See http://docs.getmoto.org/en/latest/docs/getting_started.html#what-about-those-pesky-imports
    from hls_lpdaac.historical.index import _handler

    _handler(s3_event, sqs_queue.url)
    # We expect only 1 message, but we set MaxNumberOfMessages > 1 to allow us
    # to fail the test if there are multiple messages.
    messages = sqs_queue.receive_messages(MaxNumberOfMessages=10)
    expected_message = s3_object.get()["Body"].read().decode("utf-8")

    assert len(messages) == 1
    assert messages[0].body == expected_message
