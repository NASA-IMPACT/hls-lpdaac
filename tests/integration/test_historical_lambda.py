from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mypy_boto3_lambda import LambdaClient
    from mypy_boto3_s3 import S3ServiceResource
    from mypy_boto3_s3.service_resource import Bucket
    from mypy_boto3_sqs import SQSServiceResource
    from mypy_boto3_sqs.service_resource import Queue
    from mypy_boto3_ssm import SSMClient


def test_notification(
    lambda_: LambdaClient,
    s3: S3ServiceResource,
    sqs: SQSServiceResource,
    ssm: SSMClient,
) -> None:
    # Get source bucket
    bucket_name = ssm.get_parameter(Name="/hls/tests/historical-bucket-name")[
        "Parameter"
    ].get("Value")
    assert bucket_name is not None
    bucket: "Bucket" = s3.Bucket(bucket_name)

    # Get destination queue
    queue_name = ssm.get_parameter(Name="/hls/tests/historical-queue-name")[
        "Parameter"
    ].get("Value")
    assert queue_name is not None
    queue: "Queue" = sqs.get_queue_by_name(QueueName=queue_name)

    # Write S3 Object with .v2.0.json suffix to source bucket to trigger notification.
    body = '{ "greeting": "hello world!" }'
    obj = bucket.Object("greeting.v2.0.json")
    obj.put(Body=body)
    obj.wait_until_exists()

    try:
        # Wait for lambda function to succeed, which should be triggered by S3
        # notification of object created in bucket above.
        name = ssm.get_parameter(Name="/hls/tests/historical-function-name")[
            "Parameter"
        ].get("Value")
        assert name is not None
        waiter = lambda_.get_waiter("function_active_v2")
        waiter.wait(FunctionName=name, WaiterConfig={"Delay": 5, "MaxAttempts": 20})

        # Receive message from destination queue, which should be sent by Lambda
        # function above.
        messages = queue.receive_messages(WaitTimeSeconds=20)
    finally:
        # Cleanup S3 Object with .v2.0.json suffix from source bucket.
        obj.delete()
        obj.wait_until_not_exists()

    # Assert message contents == S3 Object contents (written above)
    assert len(messages) == 1
    assert messages[0].body == body
