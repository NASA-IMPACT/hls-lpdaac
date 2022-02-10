from typing import TYPE_CHECKING

from aws_cdk import assertions
from aws_cdk import core as cdk

from hls_lpdaac.hls_lpdaac_stack import HlsLpdaacStack

if TYPE_CHECKING:
    from mypy_boto3_s3.service_resource import Bucket
    from mypy_boto3_sqs.service_resource import Queue


def test_lambda_environment(s3_bucket: "Bucket", sqs_queue: "Queue"):
    app = cdk.App()
    stack = HlsLpdaacStack(
        app,
        "hls-lpdaac",
        bucket_name=s3_bucket.name,
        queue_url=sqs_queue.url,
    )

    template = assertions.Template.from_stack(stack)
    template.has_resource_properties(
        "AWS::Lambda::Function",
        dict(Environment=dict(Variables=dict(QUEUE_URL=sqs_queue.url))),
    )
