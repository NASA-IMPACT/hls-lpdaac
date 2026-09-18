from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from aws_cdk import App
from aws_cdk.assertions import Match, Template

from cdk.stacks import HistoricalNotificationStack

if TYPE_CHECKING:
    from mypy_boto3_s3.service_resource import Bucket
    from mypy_boto3_sqs.service_resource import Queue


def _template(s3_bucket: "Bucket", sqs_queue: "Queue", **kwargs: Any) -> Template:
    app = App()
    stack = HistoricalNotificationStack(
        app,
        "hls-lpdaac",
        bucket_name=s3_bucket.name,
        queue_arn=sqs_queue.attributes["QueueArn"],
        **kwargs,
    )
    return Template.from_stack(stack)


def test_lambda_environment(s3_bucket: "Bucket", sqs_queue: "Queue"):
    template = _template(s3_bucket, sqs_queue)

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
                "Variables": {"QUEUE_URL": Match.object_like({"Fn::Join": args})}
            }
        },
    )


def test_creates_notification_queue_with_dead_letter_queue(
    s3_bucket: "Bucket", sqs_queue: "Queue"
):
    template = _template(s3_bucket, sqs_queue)

    # The notification queue and its DLQ, plus nothing else -- the LPDAAC queue
    # is imported by ARN, not created.
    template.resource_count_is("AWS::SQS::Queue", 2)
    template.has_resource_properties(
        "AWS::SQS::Queue",
        {
            "MessageRetentionPeriod": 1209600,
            "VisibilityTimeout": 180,
            "RedrivePolicy": Match.object_like({"maxReceiveCount": 3}),
        },
    )


def test_bucket_notifies_the_queue_not_the_lambda(
    s3_bucket: "Bucket", sqs_queue: "Queue"
):
    template = _template(s3_bucket, sqs_queue)

    template.has_resource_properties(
        "Custom::S3BucketNotifications",
        {
            "NotificationConfiguration": Match.object_like(
                {"QueueConfigurations": Match.any_value()}
            )
        },
    )


def test_event_source_mapping_defaults_to_enabled(
    s3_bucket: "Bucket", sqs_queue: "Queue"
):
    template = _template(s3_bucket, sqs_queue)

    template.has_resource_properties(
        "AWS::Lambda::EventSourceMapping",
        {
            "Enabled": True,
            "BatchSize": 10,
            "FunctionResponseTypes": ["ReportBatchItemFailures"],
            "ScalingConfig": {"MaximumConcurrency": 5},
        },
    )


def test_paused_disables_the_event_source_mapping(
    s3_bucket: "Bucket", sqs_queue: "Queue"
):
    template = _template(s3_bucket, sqs_queue, paused=True)

    template.has_resource_properties(
        "AWS::Lambda::EventSourceMapping", {"Enabled": False}
    )


def test_max_concurrency_is_configurable(s3_bucket: "Bucket", sqs_queue: "Queue"):
    template = _template(s3_bucket, sqs_queue, max_concurrency=25)

    template.has_resource_properties(
        "AWS::Lambda::EventSourceMapping",
        {"ScalingConfig": {"MaximumConcurrency": 25}},
    )
