from __future__ import annotations

from typing import Callable

import pytest
from mypy_boto3_s3.service_resource import Object
from mypy_boto3_sqs.service_resource import Queue

from . import make_s3_event


@pytest.mark.parametrize(
    ("prefix", "expect_tiler_message"),
    (("L30", True), ("S30", True), ("L30_VI", False), ("S30_VI", False)),
)
def test_lpdaac_forward_handler(
    prefix: str,
    expect_tiler_message: bool,
    make_s3_object_with_prefix: Callable[[str], Object],
    sqs_queue: Queue,
) -> None:
    # Import here (rather than at top level) to ensure AWS mocks are established.
    # See http://docs.getmoto.org/en/latest/docs/getting_started.html#what-about-those-pesky-imports
    from hls_lpdaac.forward import _handler

    s3_object = make_s3_object_with_prefix(prefix)
    s3_event = make_s3_event(s3_object)
    _handler(s3_event, lpdaac_queue_url=sqs_queue.url, tiler_queue_url=sqs_queue.url)

    bucket = s3_event["Records"][0]["s3"]["bucket"]["name"]  # type: ignore
    key = s3_event["Records"][0]["s3"]["object"]["key"]  # type: ignore
    messages = {
        message.body for message in sqs_queue.receive_messages(MaxNumberOfMessages=10)
    }
    expected_messages = {
        s3_object.get()["Body"].read().decode("utf-8"),
        *(
            [f"s3://{bucket}/{key.replace('.json', '_stac.json')}"]
            if expect_tiler_message
            else []
        ),
    }

    assert messages == expected_messages
