from __future__ import annotations

import json
from typing import TYPE_CHECKING, Iterator
from urllib.parse import unquote_plus

if TYPE_CHECKING:  # pragma: no cover
    from aws_lambda_typing.events import SQSEvent


def s3_object_refs(event: "SQSEvent") -> Iterator[tuple[str, str, str]]:
    """Yield (message_id, bucket, key) for every S3 object in an SQS event.

    Each SQS record body is a JSON-encoded S3 event notification envelope, so
    S3 records sit one level below the SQS records.

    S3 posts an s3:TestEvent when a queue notification is configured; it has no
    Records and yields nothing.

    Object keys in S3 event notifications are URL-encoded and are decoded here.
    """
    # SQSMessage is declared total=False, but SQS always supplies body and
    # messageId, so the not-required-key errors are ignored.
    for record in event["Records"]:
        body = json.loads(record["body"])  # type: ignore
        for s3_record in body.get("Records", []):
            s3 = s3_record["s3"]
            yield (
                record["messageId"],  # type: ignore
                s3["bucket"]["name"],
                unquote_plus(s3["object"]["key"]),
            )
