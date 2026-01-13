from __future__ import annotations

from typing import Callable

import pytest
from mypy_boto3_s3.service_resource import Object
from mypy_boto3_sqs.service_resource import Queue

from . import make_s3_event


@pytest.mark.parametrize(
    "prefix",
    ["L30", "S30", "L30_VI", "S30_VI"],
)
def test_lpdaac_forward_handler(
    prefix: str,
    make_s3_object_with_prefix: Callable[[str], Object],
    sqs_queue: Queue,
) -> None:
    # Import here (rather than at top level) to ensure AWS mocks are established.
    # See http://docs.getmoto.org/en/latest/docs/getting_started.html#what-about-those-pesky-imports
    from hls_lpdaac.forward import _handler

    s3_object = make_s3_object_with_prefix(prefix)
    s3_event = make_s3_event(s3_object)
    _handler(s3_event, lpdaac_queue_url=sqs_queue.url)

    messages = {
        message.body for message in sqs_queue.receive_messages(MaxNumberOfMessages=10)
    }
    expected_messages = {
        s3_object.get()["Body"].read().decode("utf-8"),
    }

    assert messages == expected_messages
