import os
from typing import TYPE_CHECKING

import boto3

if TYPE_CHECKING:
    from aws_lambda_typing.context import Context
    from aws_lambda_typing.events import S3Event

s3 = boto3.resource("s3")


def handler(event: "S3Event", _: "Context") -> None:
    _handler(event, os.environ["QUEUE_URL"])


# Enables unit testing without the need to monkeypatch `os.environ` (which would
# be necessary to test `handler` above).
def _handler(event: "S3Event", queue_url: str) -> None:
    # The S3Event type is not quite correct, so we are forced to ignore a couple
    # of typing errors that would not occur if the type were defined correctly.
    s3_object = event["Records"][0]["s3"]  # type: ignore
    bucket = s3_object["bucket"]["name"]
    key = s3_object["object"]["key"]  # type: ignore

    message = s3.Object(bucket, key).get()["Body"].read().decode("utf-8")

    region_name = queue_url.split(".")[1]
    sqs = boto3.client("sqs", region_name=region_name)
    response = sqs.send_message(QueueUrl=queue_url, MessageBody=message)
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]

    print(f"Status Code - {status_code} - {key}")
