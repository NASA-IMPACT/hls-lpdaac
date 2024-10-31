from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mypy_boto3_lambda import LambdaClient
    from mypy_boto3_s3 import S3ServiceResource
    from mypy_boto3_sqs import SQSServiceResource
    from mypy_boto3_ssm import SSMClient


def test_notification(
    lambda_: LambdaClient,
    s3: S3ServiceResource,
    sqs: SQSServiceResource,
    ssm: SSMClient,
) -> None:
    # Get source bucket
    bucket_name = ssm_param_value(ssm, "/hls/tests/forward-bucket-name")
    bucket = s3.Bucket(bucket_name)

    # Get forward notification queue
    forward_queue_name = ssm_param_value(ssm, "/hls/tests/forward-queue-name")
    forward_queue = sqs.get_queue_by_name(QueueName=forward_queue_name)

    # Get tiler queue
    tiler_queue_name = ssm_param_value(ssm, "/hls/tests/tiler-queue-name")
    tiler_queue = sqs.get_queue_by_name(QueueName=tiler_queue_name)

    # Write S3 Object with .v2.0.json suffix to source bucket to trigger notification.
    body = '{ "greeting": "hello world!" }'
    json_key = "greeting.v2.0.json"
    obj = bucket.Object(json_key)
    obj.put(Body=body)
    obj.wait_until_exists()

    try:
        # Wait for lambda function to succeed, which should be triggered by S3
        # notification of object created in bucket above.
        name = ssm_param_value(ssm, "/hls/tests/forward-function-name")
        waiter = lambda_.get_waiter("function_active_v2")
        waiter.wait(FunctionName=name, WaiterConfig={"Delay": 5, "MaxAttempts": 20})

        # Receive message from destination queue, which should be sent by Lambda
        # function above.
        forward_messages = forward_queue.receive_messages(
            MaxNumberOfMessages=10, WaitTimeSeconds=20
        )
        tiler_messages = tiler_queue.receive_messages(
            MaxNumberOfMessages=10, WaitTimeSeconds=20
        )
    finally:
        # Cleanup S3 Object with .v2.0.json suffix from source bucket.
        obj.delete()
        obj.wait_until_not_exists()

    # Assert message contents == S3 Object contents (written above)
    assert len(forward_messages) == 1
    assert forward_messages[0].body == body

    # Assert message contents == S3 Object contents (written above)
    assert len(tiler_messages) == 1
    assert (
        tiler_messages[0].body
        == f"s3://{bucket_name}/{json_key.replace('.json', '_stac.json')}"
    )


def ssm_param_value(ssm: SSMClient, name: str) -> str:
    value = ssm.get_parameter(Name=name)["Parameter"].get("Value")
    assert value is not None  # make type checker happy

    return value
