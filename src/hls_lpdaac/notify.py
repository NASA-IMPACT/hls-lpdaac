from __future__ import annotations

import json
from typing import TYPE_CHECKING

from hls_lpdaac.aws import s3_resource, sqs_client
from hls_lpdaac.cnm import add_provider
from hls_lpdaac.events import s3_object_refs

if TYPE_CHECKING:  # pragma: no cover
    from aws_lambda_typing.events import SQSEvent


def forward_notifications(
    event: "SQSEvent",
    *,
    queue_url: str,
    provider: str,
) -> dict:
    """Forward every CNM manifest referenced by an SQS event to an LPDAAC queue.

    Each manifest is read from S3, stamped with the provider naming the queue
    it is bound for, and sent on.

    Returns the batch item failures for the messages that could not be
    forwarded, so that only those are retried and, eventually, dead-lettered.
    """
    failures: list[dict[str, str]] = []

    for message_id, bucket, key in s3_object_refs(event):
        try:
            body = s3_resource().Object(bucket, key).get()["Body"].read().decode("utf-8")
            message = add_provider(json.loads(body), provider)
            _send_message(queue_url, key=key, message=json.dumps(message))
        except Exception as e:
            print(f"Failed to forward s3://{bucket}/{key} - {e!r}")
            failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": failures}


def _send_message(queue_url: str, *, key: str, message: str) -> None:
    region_name = queue_url.split(".")[1]
    response = sqs_client(region_name).send_message(
        QueueUrl=queue_url, MessageBody=message
    )
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    print(f"Status Code - {status_code} - {key}")
