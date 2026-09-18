import json

from aws_lambda_typing.events import S3Event, SQSEvent
from mypy_boto3_s3.service_resource import Object


def make_s3_event(s3_object: Object) -> S3Event:
    return {
        "Records": [
            {
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "",
                    "bucket": {
                        "name": f"{s3_object.bucket_name}",
                        "ownerIdentity": {
                            "principalId": "",
                        },
                        "arn": "",
                    },
                    "object": {
                        "key": f"{s3_object.key}",
                        "size": s3_object.content_length,
                        "eTag": s3_object.e_tag,
                        "versionId": s3_object.version_id,
                        "sequencer": "",
                    },
                },
            },
        ],
    }


def make_sqs_event(s3_object: Object, message_id: str = "m1") -> SQSEvent:
    return {
        "Records": [
            {
                "messageId": message_id,
                "receiptHandle": "",
                "body": json.dumps(make_s3_event(s3_object)),
                "attributes": {},
                "messageAttributes": {},
                "md5OfBody": "",
                "eventSource": "aws:sqs",
                "eventSourceARN": "",
                "awsRegion": "us-east-1",
            }
        ]
    }
