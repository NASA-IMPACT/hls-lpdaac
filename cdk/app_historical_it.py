#!/usr/bin/env python3
import os

from aws_cdk import App, Tags
from aws_cdk import aws_ssm as ssm

from stacks import HistoricalNotificationITStack, HistoricalNotificationStack

managed_policy_name = os.getenv("HLS_LPDAAC_MANAGED_POLICY_NAME")

app = App()

it_stack = HistoricalNotificationITStack(
    app,
    "hls-historical-it-resources",
    managed_policy_name=managed_policy_name,
)
stack_under_test = HistoricalNotificationStack(
    app,
    "hls-historical-under-test",
    bucket_name=it_stack.bucket.bucket_name,
    queue_arn=it_stack.queue.queue_arn,
    managed_policy_name=managed_policy_name,
)

# Set SSM Parameter for use within integration tests

ssm.StringParameter(
    stack_under_test,
    "historical-function-name",
    string_value=stack_under_test.lpdaac_historical_lambda.function_name,
    parameter_name=("/hls/tests/historical-function-name"),
)

for k, v in dict(
    Project="hls",
    App="historical-it",
).items():
    Tags.of(app).add(k, v, apply_to_launched_instances=True)

app.synth()
