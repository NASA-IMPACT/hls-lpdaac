from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aws_lambda_typing.events import S3Event
    from mypy_boto3_s3.service_resource import Object
    from mypy_boto3_sqs.service_resource import Queue


def test_lpdaac_forward_handler(
    s3_event: S3Event,
    s3_object: Object,
    sqs_queue: Queue,
) -> None:
    # Import here (rather than at top level) to ensure AWS mocks are established.
    # See http://docs.getmoto.org/en/latest/docs/getting_started.html#what-about-those-pesky-imports
    from hls_lpdaac.forward import _handler

    _handler(s3_event, lpdaac_queue_url=sqs_queue.url, tiler_queue_url=sqs_queue.url)

    bucket = s3_event["Records"][0]["s3"]["bucket"]["name"]  # type: ignore
    key = s3_event["Records"][0]["s3"]["object"]["key"]  # type: ignore
    messages = [
        message.body for message in sqs_queue.receive_messages(MaxNumberOfMessages=10)
    ]
    expected_messages = [
        s3_object.get()["Body"].read().decode("utf-8"),
        f"s3://{bucket}/{key.replace('.json', '_stac.json')}",
    ]

    assert messages == expected_messages
