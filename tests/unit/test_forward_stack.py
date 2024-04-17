from typing import TYPE_CHECKING
from urllib.parse import urlparse

from aws_cdk import App
from aws_cdk.assertions import Match, Template

from cdk.stacks import ForwardNotificationStack

if TYPE_CHECKING:
    from mypy_boto3_s3.service_resource import Bucket
    from mypy_boto3_sqs.service_resource import Queue


def test_lambda_environment(s3_bucket: "Bucket", sqs_queue: "Queue"):
    app = App()
    stack = ForwardNotificationStack(
        app,
        "forward-notification",
        bucket_name=s3_bucket.name,
        lpdaac_queue_arn=sqs_queue.attributes["QueueArn"],
        tiler_queue_arn=sqs_queue.attributes["QueueArn"],
    )

    template = Template.from_stack(stack)

    # This is ugly, but is currently necessary until (if ever) the CDK provides
    # a more convenient means for matching expected values against unresolved
    # Cfn intrinsic functions.  In this case, the queue URL is not a string
    # value, but rather an unresolved occurrence of the Fn::Join intrinsic
    # function, and the only argument we can reliably match against is the
    # object {"Ref": "AWS::URLSuffix"}.
    #
    # See https://github.com/aws/aws-cdk/issues/17938

    path = urlparse(sqs_queue.url).path
    args = Match.array_with([Match.array_with([Match.string_like_regexp(f"{path}$")])])

    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Environment": {
                "Variables": {
                    "LPDAAC_QUEUE_URL": Match.object_like({"Fn::Join": args}),
                    "TILER_QUEUE_URL": Match.object_like({"Fn::Join": args}),
                }
            }
        },
    )
