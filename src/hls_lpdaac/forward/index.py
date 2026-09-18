from __future__ import annotations

import os
from typing import TYPE_CHECKING

import boto3

from hls_lpdaac.events import s3_object_refs

if TYPE_CHECKING:  # pragma: no cover
    from aws_lambda_typing.context import Context
    from aws_lambda_typing.events import SQSEvent

s3 = boto3.resource("s3")


def handler(event: "SQSEvent", _: "Context") -> dict:
    return _handler(  # pragma: no cover
        event,
        lpdaac_queue_url=os.environ["LPDAAC_QUEUE_URL"],
    )


# Enables unit testing without the need to monkeypatch `os.environ` (which would
# be necessary to test `handler` above).
def _handler(event: "SQSEvent", *, lpdaac_queue_url: str) -> dict:
    failures: list[dict[str, str]] = []

    for message_id, bucket, key in s3_object_refs(event):
        try:
            message = s3.Object(bucket, key).get()["Body"].read().decode("utf-8")
            _send_message(lpdaac_queue_url, key=key, message=message)
        except Exception as e:
            print(f"Failed to forward s3://{bucket}/{key} - {e!r}")
            failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": failures}


def _send_message(queue_url: str, *, key: str, message: str) -> None:
    region_name = queue_url.split(".")[1]
    sqs = boto3.client("sqs", region_name=region_name)
    response = sqs.send_message(QueueUrl=queue_url, MessageBody=message)
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    print(f"Status Code - {status_code} - {key}")
