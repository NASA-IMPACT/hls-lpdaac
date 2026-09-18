from typing import Optional

from aws_cdk import Duration, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lambda_event_sources as lambda_event_sources
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_notifications as s3n
from aws_cdk import aws_sqs as sqs
from constructs import Construct

LAMBDA_TIMEOUT = Duration.seconds(30)


class NotificationStack(Stack):
    def __init__(
        self,
        scope: Construct,
        stack_name: str,
        *,
        bucket_name: str,
        lpdaac_queue_arn: str,
        managed_policy_name: Optional[str] = None,
        paused: bool = False,
        max_concurrency: int = 5,
        batch_size: int = 10,
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

        self.notification_dead_letter_queue = sqs.Queue(
            self,
            "NotificationDLQ",
            retention_period=Duration.days(14),
        )
        # A visibility timeout below the function timeout would redeliver a
        # message while the first invocation is still forwarding it.
        self.notification_queue = sqs.Queue(
            self,
            "NotificationQueue",
            retention_period=Duration.days(14),
            visibility_timeout=Duration.seconds(6 * LAMBDA_TIMEOUT.to_seconds()),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=self.notification_dead_letter_queue,
            ),
        )

        self.notification_function = lambda_.Function(
            self,
            "ForwardNotifier",
            code=lambda_.Code.from_asset("src/hls_lpdaac"),
            handler="forward.index.handler",
            runtime=lambda_.Runtime.PYTHON_3_12,
            memory_size=128,
            timeout=LAMBDA_TIMEOUT,
            environment=dict(
                LPDAAC_QUEUE_URL=self.lpdaac_queue.queue_url,
            ),
        )

        # Wire everything up

        self.notification_function.add_event_source(
            lambda_event_sources.SqsEventSource(
                self.notification_queue,
                batch_size=batch_size,
                max_concurrency=max_concurrency,
                report_batch_item_failures=True,
                enabled=not paused,
            )
        )

        self.lpdaac_queue.grant_send_messages(self.notification_function)
        self.bucket.grant_read(self.notification_function)
        self.bucket.add_object_created_notification(
            s3n.SqsDestination(self.notification_queue),  # type: ignore
            s3.NotificationKeyFilter(suffix=".v2.0.json"),
        )
