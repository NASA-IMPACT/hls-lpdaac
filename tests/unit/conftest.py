from __future__ import annotations

import json
import os
from typing import Any, Callable, Iterator

import boto3
import pytest
from moto import mock_aws
from mypy_boto3_s3 import S3ServiceResource
from mypy_boto3_s3.service_resource import Bucket, Object
from mypy_boto3_sqs import SQSServiceResource
from mypy_boto3_sqs.service_resource import Queue

CNM_MANIFEST: dict[str, Any] = {
    "collection": "HLSS30",
    "identifier": "test-job",
    "duplicationid": "HLS.S30.T01LAH.2020097T222759.v2.0",
    "version": "1.4",
    "submissionTime": "2026-09-17T00:00:00Z",
    "product": {
        "name": "HLS.S30.T01LAH.2020097T222759.v2.0",
        "dataVersion": "2.0",
        "id": "HLS.S30.T01LAH.2020097T222759.v2.0",
        "files": [
            {
                "name": "HLS.S30.T01LAH.2020097T222759.v2.0.B01.tif",
                "size": 1,
                "checksum": "0" * 128,
                "checksumType": "SHA512",
                "uri": "s3://hls-global/HLS.S30.T01LAH.2020097T222759.v2.0.B01.tif",
                "type": "data",
            }
        ],
    },
}


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="function")
def s3(aws_credentials) -> Iterator[S3ServiceResource]:
    with mock_aws():
        yield boto3.resource("s3")


@pytest.fixture(scope="function")
def s3_bucket(s3: S3ServiceResource) -> Bucket:
    bucket = s3.Bucket("mybucket")
    bucket.create()

    return bucket


@pytest.fixture(scope="function")
def make_s3_object_with_prefix(s3_bucket: Bucket) -> Callable[[str], Object]:
    def go(prefix: str) -> Object:
        return s3_bucket.put_object(
            Key=f"{prefix.rstrip('/')}/myobject.v2.0.json",
            Body=json.dumps(CNM_MANIFEST).encode("utf-8"),
        )

    return go


@pytest.fixture(scope="function")
def sqs(aws_credentials) -> Iterator[SQSServiceResource]:
    with mock_aws():
        yield boto3.resource("sqs")


@pytest.fixture(scope="function")
def sqs_queue(sqs: SQSServiceResource) -> Queue:
    return sqs.create_queue(QueueName="myqueue")
