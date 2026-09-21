from __future__ import annotations

import json

from mypy_boto3_lambda import LambdaClient
from mypy_boto3_s3 import S3ServiceResource
from mypy_boto3_sqs import SQSServiceResource
from mypy_boto3_ssm import SSMClient

from .helpers import fetch_messages, remaining_messages, ssm_param_value


def test_notification(
    lambda_: LambdaClient,
    s3: S3ServiceResource,
    sqs: SQSServiceResource,
    ssm: SSMClient,
) -> None:
    # Get source bucket
    bucket_name = ssm_param_value(ssm, "/hls/tests/historical-bucket-name")
    bucket = s3.Bucket(bucket_name)

    # Get destination queue
    queue_name = ssm_param_value(ssm, "/hls/tests/historical-queue-name")
    queue = sqs.get_queue_by_name(QueueName=queue_name)

    # Write S3 Object with .v2.0.json suffix to source bucket to trigger notification.
    body = '{ "greeting": "hello world!" }'
    obj = bucket.Object("greeting.v2.0.json")
    obj.put(Body=body)
    obj.wait_until_exists()

    try:
        # Wait for the lambda function to finish deploying before expecting it
        # to drain the notification queue.
        name = ssm_param_value(ssm, "/hls/tests/historical-function-name")
        waiter = lambda_.get_waiter("function_active_v2")
        waiter.wait(FunctionName=name, WaiterConfig={"Delay": 5, "MaxAttempts": 20})

        messages = fetch_messages(queue, expected=1)
        extra_messages = remaining_messages(queue)
    finally:
        # Cleanup S3 Object with .v2.0.json suffix from source bucket.
        obj.delete()
        obj.wait_until_not_exists()

    # Assert message contents == S3 Object contents (written above), plus the
    # provider naming the LPDAAC queue the forwarder publishes to.
    expected = {**json.loads(body), "provider": "lp_HLS_2.0_BACKWARD_PROCESSED"}

    assert [json.loads(message) for message in messages] == [expected]
    assert extra_messages == []
