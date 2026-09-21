from __future__ import annotations

import json
from typing import Sequence

from mypy_boto3_s3 import S3ServiceResource
from mypy_boto3_s3.service_resource import Bucket, Object
from mypy_boto3_sqs import SQSServiceResource
from mypy_boto3_ssm import SSMClient

from .helpers import fetch_messages, remaining_messages, ssm_param_value


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

    body = '{ "greeting": "hello world!" }'
    objects = write_objects(bucket, body)

    try:
        # We expect 4 messages, 2 for regular and 2 for VI
        forward_messages = fetch_messages(forward_queue, expected=4)
        extra_messages = remaining_messages(forward_queue)
    finally:
        # Cleanup S3 Object with .v2.0.json suffix from source bucket.
        for obj in objects:
            obj.delete()
            obj.wait_until_not_exists()

    # The forwarder adds the provider naming the LPDAAC queue it publishes to.
    expected = {**json.loads(body), "provider": "lp_HLS_2.0_FORWARD_PROCESSED"}

    assert [json.loads(message) for message in forward_messages] == [expected] * 4
    assert extra_messages == []


def write_objects(bucket: Bucket, body: str) -> Sequence[Object]:
    # Write S3 Objects with .v2.0.json suffix to source bucket to trigger notification.
    # We expect 4 messages in the forward queue

    objects = [
        bucket.Object(f"{prefix}/greeting.v2.0.json")
        for prefix in ("L30", "S30", "L30_VI", "S30_VI")
    ]

    for obj in objects:
        obj.put(Body=body)
        obj.wait_until_exists()

    return objects
