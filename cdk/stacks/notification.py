from typing import NamedTuple

from aws_cdk import Duration, Stack
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as events_targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lambda_event_sources as lambda_event_sources
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_notifications as s3n
from aws_cdk import aws_sqs as sqs
from constructs import Construct

ASSET_ROOT = "src"
DLQ_ALERT_HANDLER = "hls_lpdaac.dlq_alert.handler"
LAMBDA_TIMEOUT = Duration.seconds(30)


class ConstructIds(NamedTuple):
    """Construct ids for one deployment variant.

    Construct ids determine CloudFormation logical ids, so these differ between
    the forward and historical stacks for historical reasons and must not be
    changed: renaming one replaces the resource, and replacing a queue discards
    the notifications still in it.
    """

    bucket: str
    lpdaac_queue: str
    dead_letter_queue: str
    notification_queue: str
    function: str


class NotificationStack(Stack):
    """Forward S3 object-created notifications to an LPDAAC queue.

    S3 notifies a queue owned by this stack, which the forwarder Lambda
    consumes through an event source mapping. That buffer is what lets
    notifications survive an LPDAAC maintenance window, and what bounds the
    rate at which they reach LPDAAC.

    The forward and historical deployments differ only in naming, so they share
    this definition and supply their own ids, handler, and queue URL variable.
    """

    def __init__(
        self,
        scope: Construct,
        stack_name: str,
        *,
        bucket_name: str,
        queue_arn: str,
        ids: ConstructIds,
        handler: str,
        queue_url_variable: str,
        managed_policy_name: None | str = None,
        paused: bool = False,
        max_concurrency: int = 5,
        batch_size: int = 10,
        slack_webhook_url: None | str = None,
        dlq_alert_schedule: None | events.Schedule = None,
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

        self.bucket = s3.Bucket.from_bucket_name(self, ids.bucket, bucket_name)
        self.lpdaac_queue = sqs.Queue.from_queue_arn(
            self, ids.lpdaac_queue, queue_arn=queue_arn
        )

        self.notification_dead_letter_queue = sqs.Queue(
            self,
            ids.dead_letter_queue,
            retention_period=Duration.days(14),
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            enforce_ssl=True,
        )
        # A visibility timeout below the function timeout would redeliver a
        # message while the first invocation is still forwarding it.
        self.notification_queue = sqs.Queue(
            self,
            ids.notification_queue,
            retention_period=Duration.days(14),
            visibility_timeout=Duration.seconds(6 * LAMBDA_TIMEOUT.to_seconds()),
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            enforce_ssl=True,
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=self.notification_dead_letter_queue,
            ),
        )

        self.notification_function = lambda_.Function(
            self,
            ids.function,
            code=lambda_.Code.from_asset(
                ASSET_ROOT,
                exclude=["**/__pycache__", "*.egg-info"],
            ),
            handler=handler,
            runtime=lambda_.Runtime.PYTHON_3_12,
            memory_size=128,
            timeout=LAMBDA_TIMEOUT,
            environment={queue_url_variable: self.lpdaac_queue.queue_url},
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

        # A dead-letter queue nobody watches is a delete, so alert on its depth.
        # The resources always exist; without a webhook the schedule is created
        # disabled, so turning alerting on is a configuration change rather than
        # a create/delete of the function and its rule.
        alert_state_ssm_path = f"/{stack_name}/dlq-alert-state"
        self.dlq_alert_function = lambda_.Function(
            self,
            "DlqAlert",
            code=lambda_.Code.from_asset(
                ASSET_ROOT,
                exclude=["**/__pycache__", "*.egg-info"],
            ),
            handler=DLQ_ALERT_HANDLER,
            runtime=lambda_.Runtime.PYTHON_3_12,
            memory_size=128,
            timeout=Duration.seconds(30),
            environment=dict(
                DLQ_URL=self.notification_dead_letter_queue.queue_url,
                SLACK_WEBHOOK_URL=slack_webhook_url or "",
                ALERT_STATE_SSM_PATH=alert_state_ssm_path,
                STACK_NAME=stack_name,
            ),
        )
        self.notification_dead_letter_queue.grant(
            self.dlq_alert_function, "sqs:GetQueueAttributes"
        )
        self.dlq_alert_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter", "ssm:PutParameter"],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}"
                    f":parameter{alert_state_ssm_path}"
                ],
            )
        )
        events.Rule(
            self,
            "DlqAlertSchedule",
            schedule=dlq_alert_schedule or events.Schedule.rate(Duration.minutes(15)),
            targets=[events_targets.LambdaFunction(self.dlq_alert_function)],
            enabled=bool(slack_webhook_url),
        )
