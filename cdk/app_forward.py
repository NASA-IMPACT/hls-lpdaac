#!/usr/bin/env python3
import os

from aws_cdk import App, Tags

from stacks import ForwardNotificationStack

# Required environment variables
stack_name = os.environ["HLS_LPDAAC_STACK"]
bucket_name = os.environ["HLS_LPDAAC_BUCKET_NAME"]
queue_arn = os.environ["HLS_LPDAAC_QUEUE_ARN"]

# Optional environment variables
managed_policy_name = os.getenv("HLS_LPDAAC_MANAGED_POLICY_NAME")
# Optional, but if it is not provided, the tiler queue will be created, which
# is what we want in all environments except production since there is only a
# single tiler queue.
tiler_queue_arn = os.getenv("HLS_LPDAAC_TILER_QUEUE_ARN")

app = App()

ForwardNotificationStack(
    app,
    stack_name,
    bucket_name=bucket_name,
    lpdaac_queue_arn=queue_arn,
    tiler_queue_arn=tiler_queue_arn,
    managed_policy_name=managed_policy_name,
)

for k, v in dict(
    Project="hls",
    Stack=stack_name,
).items():
    Tags.of(app).add(k, v, apply_to_launched_instances=True)

app.synth()
