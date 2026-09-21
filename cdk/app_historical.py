#!/usr/bin/env python3
import os

from aws_cdk import App, Duration, Tags
from aws_cdk import aws_events as events

from stacks import HistoricalNotificationStack

# Required environment variables
stack_name = os.environ["HLS_LPDAAC_STACK"]
bucket_name = os.environ["HLS_LPDAAC_BUCKET_NAME"]
queue_arn = os.environ["HLS_LPDAAC_QUEUE_ARN"]

# Optional environment variables
managed_policy_name = os.getenv("HLS_LPDAAC_MANAGED_POLICY_NAME")
paused = os.getenv("HLS_LPDAAC_PAUSED", "false").lower() in ("1", "true", "yes")
max_concurrency = int(os.getenv("HLS_LPDAAC_MAX_CONCURRENCY", "5"))
batch_size = int(os.getenv("HLS_LPDAAC_BATCH_SIZE", "10"))
slack_webhook_url = os.getenv("HLS_LPDAAC_SLACK_ALERT_WEBHOOK")
dlq_alert_cron_minutes = int(os.getenv("HLS_LPDAAC_DLQ_ALERT_CRON_MINUTES", "15"))
dlq_alert_schedule = events.Schedule.rate(Duration.minutes(dlq_alert_cron_minutes))

app = App()

HistoricalNotificationStack(
    app,
    stack_name,
    bucket_name=bucket_name,
    queue_arn=queue_arn,
    managed_policy_name=managed_policy_name,
    paused=paused,
    max_concurrency=max_concurrency,
    batch_size=batch_size,
    slack_webhook_url=slack_webhook_url,
    dlq_alert_schedule=dlq_alert_schedule,
)

for k, v in dict(
    Project="hls",
    Stack=stack_name,
).items():
    Tags.of(app).add(k, v, apply_to_launched_instances=True)

app.synth()
