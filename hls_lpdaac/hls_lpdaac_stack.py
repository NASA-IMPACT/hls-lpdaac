import os
from typing import Optional

from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lambda_python as lambda_py
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_notifications as s3n
from aws_cdk import core as cdk


class HlsLpdaacStack(cdk.Stack):
    def __init__(
        self,
        scope: cdk.Construct,
        stack_name: str,
        *,
        bucket_name: str,
        queue_url: str,
        permissions_boundary_arn: Optional[str],
        **kwargs,
    ) -> None:
        super().__init__(scope, stack_name, **kwargs)

        if permissions_boundary_arn:
            iam.PermissionsBoundary.of(self).apply(
                iam.ManagedPolicy.from_managed_policy_arn(
                    self, "PermissionsBoundary", permissions_boundary_arn
                )
            )

        # TODO Find correct role
        self.lambda_role = iam.Role(
            self,
            "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )

        self.sqs_to_lpdaac_historical_function = lambda_py.PythonFunction(
            self,
            id="SqsToLpdaacHistorical",
            entry="hls_lpdaac/lpdaac/historical",
            runtime=lambda_.Runtime.PYTHON_3_9,
            memory_size=128,
            timeout=cdk.Duration.seconds(3),
            role=self.lambda_role,
            environment=dict(
                QUEUE_URL=queue_url,
            ),
        )

        self.bucket = s3.Bucket.from_bucket_name(
            self, "SqsToLpdaacHistoricalEventSource", bucket_name
        )

        self.bucket.add_object_created_notification(
            s3n.LambdaDestination(self.sqs_to_lpdaac_historical_function),
            s3.NotificationKeyFilter(suffix=".v2.0.json"),
        )
