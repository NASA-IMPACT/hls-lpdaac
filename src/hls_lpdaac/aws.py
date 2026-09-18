from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING

import boto3

if TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_s3.service_resource import S3ServiceResource
    from mypy_boto3_sqs import SQSClient
    from mypy_boto3_ssm import SSMClient


# Clients and resources are cached rather than built per call: construction is
# not free, and repeatedly building them grows memory, since each one registers
# its own event handlers. See https://github.com/boto/boto3/issues/1670.
#
# They are built on first use rather than at import so that importing a handler
# module touches no AWS client.


@cache
def s3_resource() -> "S3ServiceResource":
    """Return the process-wide S3 resource, building it on first use."""
    return boto3.resource("s3")


@cache
def sqs_client(region_name: str) -> "SQSClient":
    """Return the process-wide SQS client for a region, building it on first use."""
    return boto3.client("sqs", region_name=region_name)


@cache
def ssm_client() -> "SSMClient":
    """Return the process-wide SSM client, building it on first use."""
    return boto3.client("ssm")
