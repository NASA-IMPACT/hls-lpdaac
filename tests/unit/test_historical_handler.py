from __future__ import annotations

from typing import Callable

from mypy_boto3_s3.service_resource import Object
from mypy_boto3_sqs.service_resource import Queue

from . import make_s3_event


def test_lpdaac_historical_handler(
    make_s3_object_with_prefix: Callable[[str], Object],
    sqs_queue: Queue,
) -> None:
    # Import here (rather than at top level) to ensure AWS mocks are established.
    # See http://docs.getmoto.org/en/latest/docs/getting_started.html#what-about-those-pesky-imports
    from hls_lpdaac.historical.index import _handler

    s3_object = make_s3_object_with_prefix("L30/")
    s3_event = make_s3_event(s3_object)
    _handler(s3_event, sqs_queue.url)
    # We expect only 1 message, but we set MaxNumberOfMessages > 1 to allow us
    # to fail the test if there are multiple messages.
    messages = sqs_queue.receive_messages(MaxNumberOfMessages=10)
    expected_message = s3_object.get()["Body"].read().decode("utf-8")

    assert len(messages) == 1
    assert messages[0].body == expected_message
