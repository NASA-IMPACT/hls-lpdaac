from __future__ import annotations

import json

from aws_lambda_typing.events import SQSEvent
from aws_lambda_typing.events.sqs import SQSMessage

from hls_lpdaac.events import s3_object_refs


def _sqs_record(message_id: str, body: dict) -> "SQSMessage":
    return {
        "messageId": message_id,
        "receiptHandle": "",
        "body": json.dumps(body),
        "attributes": {},
        "messageAttributes": {},
        "md5OfBody": "",
        "eventSource": "aws:sqs",
        "eventSourceARN": "",
        "awsRegion": "us-west-2",
    }


def _s3_envelope(bucket: str, key: str) -> dict:
    return {
        "Records": [
            {
                "eventSource": "aws:s3",
                "s3": {
                    "bucket": {"name": bucket},
                    "object": {"key": key},
                },
            }
        ]
    }


def test_yields_one_ref_per_s3_record() -> None:
    event: "SQSEvent" = {
        "Records": [
            _sqs_record("m1", _s3_envelope("mybucket", "L30/a.v2.0.json")),
            _sqs_record("m2", _s3_envelope("mybucket", "S30/b.v2.0.json")),
        ]
    }

    assert list(s3_object_refs(event)) == [
        ("m1", "mybucket", "L30/a.v2.0.json"),
        ("m2", "mybucket", "S30/b.v2.0.json"),
    ]


def test_skips_s3_test_event() -> None:
    event: "SQSEvent" = {
        "Records": [
            _sqs_record("m1", {"Event": "s3:TestEvent", "Bucket": "mybucket"}),
            _sqs_record("m2", _s3_envelope("mybucket", "L30/a.v2.0.json")),
        ]
    }

    assert list(s3_object_refs(event)) == [("m2", "mybucket", "L30/a.v2.0.json")]


def test_unquotes_url_encoded_key() -> None:
    event: "SQSEvent" = {
        "Records": [_sqs_record("m1", _s3_envelope("b", "L30/a+b%3Dc.v2.0.json"))]
    }

    assert list(s3_object_refs(event)) == [("m1", "b", "L30/a b=c.v2.0.json")]
