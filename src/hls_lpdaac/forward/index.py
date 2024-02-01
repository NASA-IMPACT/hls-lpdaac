from __future__ import annotations

import os
from typing import TYPE_CHECKING

import boto3

if TYPE_CHECKING:
    from aws_lambda_typing.context import Context
    from aws_lambda_typing.events import S3Event

s3 = boto3.resource("s3")


def handler(event: "S3Event", _: "Context") -> None:
    return _handler(
        event,
        lpdaac_queue_url=os.environ["LPDAAC_QUEUE_URL"],
        tiler_queue_url=os.environ["TILER_QUEUE_URL"],
    )


# Enables unit testing without the need to monkeypatch `os.environ` (which would
# be necessary to test `handler` above).
def _handler(event: "S3Event", *, lpdaac_queue_url: str, tiler_queue_url: str) -> None:
    # The S3Event type is not quite correct, so we are forced to ignore a couple
    # of typing errors that would not occur if the type were defined correctly.
    s3_object = event["Records"][0]["s3"]  # type: ignore
    bucket = s3_object["bucket"]["name"]

    json_key = s3_object["object"]["key"]  # type: ignore
    json_contents = s3.Object(bucket, json_key).get()["Body"].read().decode("utf-8")
    _send_message(lpdaac_queue_url, key=json_key, message=json_contents)

    stac_json_key = json_key.replace(".json", "_stac.json")
    stac_url = f"s3://{bucket}/{stac_json_key}"
    _send_message(tiler_queue_url, key=stac_json_key, message=stac_url)


def _send_message(queue_url: str, *, key: str, message: str) -> None:
    region_name = queue_url.split(".")[1]
    sqs = boto3.client("sqs", region_name=region_name)
    response = sqs.send_message(QueueUrl=queue_url, MessageBody=message)
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    print(f"Status Code - {status_code} - {key}")
