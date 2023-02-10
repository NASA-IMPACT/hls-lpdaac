from typing import Optional

from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_ssm as ssm
from aws_cdk import core as cdk


class HlsLpdaacIntegrationStack(cdk.Stack):
    def __init__(
        self,
        scope: cdk.Construct,
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
            removal_policy=cdk.RemovalPolicy.DESTROY,
            # auto_delete_objects=True,
        )
        self.queue = sqs.Queue(self, "test-queue")

        # Set SSM Parameters for use within integration tests

        ssm.StringParameter(
            self,
            "bucket_name",
            string_value=self.bucket.bucket_name,
            parameter_name=("/tests/bucket_name"),
        )

        ssm.StringParameter(
            self,
            "queue_name",
            string_value=self.queue.queue_name,
            parameter_name=("/tests/queue_name"),
        )
