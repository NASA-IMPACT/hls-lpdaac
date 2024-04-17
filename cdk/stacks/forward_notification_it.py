from typing import Optional

from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_ssm as ssm
from constructs import Construct


class NotificationITStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        managed_policy_name: Optional[str] = None,
    ) -> None:
        super().__init__(scope, id)

        if managed_policy_name:
            iam.PermissionsBoundary.of(self).apply(
                iam.ManagedPolicy.from_managed_policy_name(
                    self,
                    "PermissionsBoundary",
                    managed_policy_name,
                )
            )

        self.bucket = s3.Bucket(
            self,
            "test-bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        self.forward_queue = sqs.Queue(self, "forward-queue")
        self.tiler_queue = sqs.Queue(self, "tiler-queue")

        # Set SSM Parameters for use within integration tests

        ssm.StringParameter(
            self,
            "bucket-name",
            string_value=self.bucket.bucket_name,
            parameter_name="/hls/tests/forward-bucket-name",
        )

        ssm.StringParameter(
            self,
            "forward-queue-name",
            string_value=self.forward_queue.queue_name,
            parameter_name="/hls/tests/forward-queue-name",
        )

        ssm.StringParameter(
            self,
            "tiler-queue-name",
            string_value=self.tiler_queue.queue_name,
            parameter_name="/hls/tests/tiler-queue-name",
        )
