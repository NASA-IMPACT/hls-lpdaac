from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from hls_lpdaac.aws import s3_resource, sqs_client
from hls_lpdaac.cnm import add_provider
from hls_lpdaac.events import s3_object_refs

if TYPE_CHECKING:  # pragma: no cover
    from aws_lambda_typing.context import Context
    from aws_lambda_typing.events import SQSEvent

# Identifies the LPDAAC queue this stack publishes to. LPDAAC matches provider
# names to their ingest queues, so the value must track the queue ARN this
# stack is deployed against.
PROVIDER = "lp_HLS_2.0_FORWARD_PROCESSED"


def handler(event: "SQSEvent", _: "Context") -> dict:
    return _handler(  # pragma: no cover
        event,
        lpdaac_queue_url=os.environ["LPDAAC_QUEUE_URL"],
    )


# Enables unit testing without the need to monkeypatch `os.environ` (which would
# be necessary to test `handler` above).
def _handler(
    event: "SQSEvent",
    *,
    lpdaac_queue_url: str,
    provider: str = PROVIDER,
) -> dict:
    failures: list[dict[str, str]] = []

    for message_id, bucket, key in s3_object_refs(event):
        try:
            body = s3_resource().Object(bucket, key).get()["Body"].read().decode("utf-8")
            message = add_provider(json.loads(body), provider)
            _send_message(lpdaac_queue_url, key=key, message=json.dumps(message))
        except Exception as e:
            print(f"Failed to forward s3://{bucket}/{key} - {e!r}")
            failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": failures}


def _send_message(queue_url: str, *, key: str, message: str) -> None:
    region_name = queue_url.split(".")[1]
    sqs = sqs_client(region_name)
    response = sqs.send_message(QueueUrl=queue_url, MessageBody=message)
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    print(f"Status Code - {status_code} - {key}")
