import os
from typing import TYPE_CHECKING, Iterator

import boto3
import pytest
from moto import mock_s3, mock_sqs

if TYPE_CHECKING:
    from aws_lambda_typing.events import S3Event
    from mypy_boto3_s3 import S3ServiceResource
    from mypy_boto3_s3.service_resource import Bucket, Object
    from mypy_boto3_sqs import SQSServiceResource
    from mypy_boto3_sqs.service_resource import Queue


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="function")
def s3(aws_credentials) -> Iterator["S3ServiceResource"]:
    with mock_s3():
        yield boto3.resource("s3")


@pytest.fixture(scope="function")
def s3_bucket(s3: "S3ServiceResource") -> "Bucket":
    bucket = s3.Bucket("mybucket")
    bucket.create()

    return bucket


@pytest.fixture(scope="function")
def s3_object(s3_bucket: "Bucket") -> "Object":
    return s3_bucket.put_object(Key="myobject.v2.json", Body=bytes("test", "utf-8"))


@pytest.fixture(scope="function")
def s3_event(s3_object: "Object") -> "S3Event":
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


@pytest.fixture(scope="function")
def sqs(aws_credentials) -> Iterator["SQSServiceResource"]:
    with mock_sqs():
        yield boto3.resource("sqs")


@pytest.fixture(scope="function")
def sqs_queue(sqs: "SQSServiceResource") -> "Queue":
    return sqs.create_queue(QueueName="myqueue")
