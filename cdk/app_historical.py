#!/usr/bin/env python3
import os

from aws_cdk import App, Tags

from stacks import HistoricalNotificationStack

# Required environment variables
stack_name = os.environ["HLS_LPDAAC_STACK"]
bucket_name = os.environ["HLS_LPDAAC_BUCKET_NAME"]
queue_arn = os.environ["HLS_LPDAAC_QUEUE_ARN"]

# Optional environment variables
managed_policy_name = os.getenv("HLS_LPDAAC_MANAGED_POLICY_NAME")

app = App()

HistoricalNotificationStack(
    app,
    stack_name,
    bucket_name=bucket_name,
    queue_arn=queue_arn,
    managed_policy_name=managed_policy_name,
)

for k, v in dict(
    Project="hls",
    Stack=stack_name,
).items():
    Tags.of(app).add(k, v, apply_to_launched_instances=True)

app.synth()
