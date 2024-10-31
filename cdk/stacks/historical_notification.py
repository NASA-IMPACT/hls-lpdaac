from typing import Optional

from aws_cdk import Duration, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_notifications as s3n
from aws_cdk import aws_sqs as sqs
from constructs import Construct


class NotificationStack(Stack):
    def __init__(
        self,
        scope: Construct,
        stack_name: str,
        *,
        bucket_name: str,
        queue_arn: str,
        managed_policy_name: Optional[str] = None,
    ) -> None:
        super().__init__(scope, stack_name)

        if managed_policy_name:
            iam.PermissionsBoundary.of(self).apply(
                iam.ManagedPolicy.from_managed_policy_name(
                    self,
                    "PermissionsBoundary",
                    managed_policy_name,
                )
            )

        self.lpdaac_historical_bucket = s3.Bucket.from_bucket_name(
            self,
            "HistoricalBucket",
            bucket_name,
        )

        self.lpdaac_historical_queue = sqs.Queue.from_queue_arn(
            self,
            "HistoricalQueue",
            queue_arn=queue_arn,
        )

        self.lpdaac_historical_lambda = lambda_.Function(
            self,
            "HistoricalLambda",
            code=lambda_.Code.from_asset("src/hls_lpdaac/historical"),
            handler="index.handler",
            runtime=lambda_.Runtime.PYTHON_3_9,  # type: ignore
            memory_size=128,
            timeout=Duration.seconds(30),
            environment=dict(QUEUE_URL=self.lpdaac_historical_queue.queue_url),
        )

        # Wire everything up

        self.lpdaac_historical_queue.grant_send_messages(self.lpdaac_historical_lambda)
        self.lpdaac_historical_bucket.grant_read(self.lpdaac_historical_lambda)
        self.lpdaac_historical_bucket.add_object_created_notification(
            s3n.LambdaDestination(self.lpdaac_historical_lambda),  # type: ignore
            s3.NotificationKeyFilter(suffix=".v2.0.json"),
        )
