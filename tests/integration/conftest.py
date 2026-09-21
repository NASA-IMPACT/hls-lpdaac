from __future__ import annotations

import boto3
import pytest
from mypy_boto3_lambda import LambdaClient
from mypy_boto3_s3 import S3ServiceResource
from mypy_boto3_sqs import SQSServiceResource
from mypy_boto3_ssm import SSMClient


@pytest.fixture
def lambda_() -> LambdaClient:
    return boto3.client("lambda")


@pytest.fixture
def s3() -> S3ServiceResource:
    return boto3.resource("s3")


@pytest.fixture
def sqs() -> SQSServiceResource:
    return boto3.resource("sqs")


@pytest.fixture
def ssm() -> SSMClient:
    return boto3.client("ssm")
