from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mypy_boto3_lambda import LambdaClient
    from mypy_boto3_s3 import S3ServiceResource
    from mypy_boto3_s3.service_resource import Bucket
    from mypy_boto3_sqs import SQSServiceResource
    from mypy_boto3_sqs.service_resource import Queue
    from mypy_boto3_ssm import SSMClient


def test_notification(
    lambda_: "LambdaClient",
    s3: "S3ServiceResource",
    sqs: "SQSServiceResource",
    ssm: "SSMClient",
) -> None:
    # Get source bucket
    bucket_name = ssm.get_parameter(Name="/tests/bucket_name")["Parameter"].get("Value")
    assert bucket_name is not None
    bucket: "Bucket" = s3.Bucket(bucket_name)

    # Get destination queue
    queue_name = ssm.get_parameter(Name="/tests/queue_name")["Parameter"].get("Value")
    assert queue_name is not None
    queue: "Queue" = sqs.get_queue_by_name(QueueName=queue_name)

    # Write S3 Object with .v2.0.json suffix to source bucket
    body = '{ "greeting": "hello world!" }'
    bucket.put_object(Key="greeting.v2.0.json", Body=body)

    # Wait for lambda function to succeed, which should be triggered by S3 notification
    # of object created in bucket above.
    func_name = ssm.get_parameter(Name="/tests/function_name")["Parameter"].get("Value")
    assert func_name is not None
    waiter = lambda_.get_waiter("function_active_v2")
    waiter.wait(FunctionName=func_name, WaiterConfig={"Delay": 5, "MaxAttempts": 10})

    # Receive message destination from queue, which should be sent by Lambda function
    # above
    messages = queue.receive_messages()

    # Assert message contents == S3 Object contents (written above)
    assert len(messages) == 1
    assert messages[0].body == body
