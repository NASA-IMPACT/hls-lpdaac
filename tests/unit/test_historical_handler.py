from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aws_lambda_typing.events import S3Event
    from mypy_boto3_s3.service_resource import Object
    from mypy_boto3_sqs.service_resource import Queue


def test_lpdaac_historical_handler(
    s3_event: "S3Event", s3_object: "Object", sqs_queue: "Queue"
) -> None:
    from hls_lpdaac.lpdaac.historical.index import _handler as handler

    handler(s3_event, sqs_queue.url)
    messages = sqs_queue.receive_messages()
    expected_message = s3_object.get()["Body"].read().decode("utf-8")

    assert len(messages) == 1
    assert messages[0].body == expected_message
