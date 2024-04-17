from typing import Optional, Union

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
        lpdaac_queue_arn: str,
        tiler_queue_arn: Optional[str] = None,
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

        # Define resources

        self.bucket = s3.Bucket.from_bucket_name(self, "hls-output", bucket_name)
        self.lpdaac_queue = sqs.Queue.from_queue_arn(
            self, "lpdaac", queue_arn=lpdaac_queue_arn
        )
        self.tiler_queue: Union[sqs.Queue, sqs.IQueue] = (
            sqs.Queue(self, "tiler", retention_period=Duration.minutes(5))
            if tiler_queue_arn is None
            else sqs.Queue.from_queue_arn(self, "tiler", queue_arn=tiler_queue_arn)
        )
        self.notification_function = lambda_.Function(
            self,
            "ForwardNotifier",
            code=lambda_.Code.from_asset("src/hls_lpdaac/forward"),
            handler="index.handler",
            runtime=lambda_.Runtime.PYTHON_3_9,  # type: ignore
            memory_size=128,
            timeout=Duration.seconds(30),
            environment=dict(
                LPDAAC_QUEUE_URL=self.lpdaac_queue.queue_url,
                TILER_QUEUE_URL=self.tiler_queue.queue_url,
            ),
        )

        # Wire everything up

        self.lpdaac_queue.grant_send_messages(self.notification_function)
        self.tiler_queue.grant_send_messages(self.notification_function)
        self.bucket.grant_read(self.notification_function)
        self.bucket.add_object_created_notification(
            s3n.LambdaDestination(self.notification_function),  # type: ignore
            s3.NotificationKeyFilter(suffix=".v2.0.json"),
        )
