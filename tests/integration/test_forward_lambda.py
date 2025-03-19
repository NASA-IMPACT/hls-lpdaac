from __future__ import annotations

from typing import Iterator, Sequence

from mypy_boto3_s3 import S3ServiceResource
from mypy_boto3_s3.service_resource import Bucket, Object
from mypy_boto3_sqs import SQSServiceResource
from mypy_boto3_sqs.service_resource import Message, Queue
from mypy_boto3_ssm import SSMClient


def test_notification(
    s3: S3ServiceResource,
    sqs: SQSServiceResource,
    ssm: SSMClient,
) -> None:
    # Get source bucket
    bucket_name = ssm_param_value(ssm, "/hls/tests/forward-bucket-name")
    bucket = s3.Bucket(bucket_name)
    forward_queue_name = ssm_param_value(ssm, "/hls/tests/forward-queue-name")
    forward_queue = sqs.get_queue_by_name(QueueName=forward_queue_name)
    tiler_queue_name = ssm_param_value(ssm, "/hls/tests/tiler-queue-name")
    tiler_queue = sqs.get_queue_by_name(QueueName=tiler_queue_name)

    body = '{ "greeting": "hello world!" }'
    objects = write_objects(bucket, body)

    try:
        forward_messages = list(fetch_messages(forward_queue))
        tiler_messages = list(fetch_messages(tiler_queue))
    finally:
        # Cleanup S3 Object with .v2.0.json suffix from source bucket.
        for obj in objects:
            obj.delete()
            obj.wait_until_not_exists()

    # We expect 4 messages, 2 for regular and 2 for VI
    assert forward_messages == [body] * 4

    # We expect only 2 messages for the 2 non-VI objects written
    assert len(tiler_messages) == 2
    assert tiler_messages == [
        f"s3://{bucket_name}/{obj.key.replace('.json', '_stac.json')}"
        for obj in objects
        if "_VI/" not in obj.key
    ]


def ssm_param_value(ssm: SSMClient, name: str) -> str:
    value = ssm.get_parameter(Name=name)["Parameter"].get("Value")
    assert value is not None  # make type checker happy

    return value


def write_objects(bucket: Bucket, body: str) -> Sequence[Object]:
    # Write S3 Objects with .v2.0.json suffix to source bucket to trigger notification.
    # We expect 4 messages in the forward queue and 2 in the tiler queue because the
    # tiler queue should not send messages for VI.

    objects = [
        bucket.Object(f"{prefix}/greeting.v2.0.json")
        for prefix in ("L30", "S30", "L30_VI", "S30_VI")
    ]

    for obj in objects:
        obj.put(Body=body)
        obj.wait_until_exists()

    return objects


def fetch_messages(queue: Queue) -> Iterator[str]:
    while messages := queue.receive_messages(
        MaxNumberOfMessages=10, WaitTimeSeconds=20
    ):
        queue.delete_messages(
            Entries=[
                {"Id": message.message_id, "ReceiptHandle": message.receipt_handle}
                for message in messages
            ]
        )

        yield from (message.body for message in messages)
