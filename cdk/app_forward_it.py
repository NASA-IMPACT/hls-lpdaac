#!/usr/bin/env python3
import os

from aws_cdk import App, Tags
from aws_cdk import aws_ssm as ssm

from stacks import ForwardNotificationITStack, ForwardNotificationStack

managed_policy_name = os.getenv("HLS_LPDAAC_MANAGED_POLICY_NAME")

app = App()

it_stack = ForwardNotificationITStack(
    app,
    "hls-forward-it-resources",
    managed_policy_name=managed_policy_name,
)
stack_under_test = ForwardNotificationStack(
    app,
    "hls-forward-under-test",
    bucket_name=it_stack.bucket.bucket_name,
    lpdaac_queue_arn=it_stack.forward_queue.queue_arn,
    tiler_queue_arn=it_stack.tiler_queue.queue_arn,
    managed_policy_name=managed_policy_name,
)

# Set SSM Parameter for use within integration tests.  Others are set directly
# within the it_stack itself.  This one is set on stack_under_test rather than
# it_stack so we don't have a cyclic dependency.

ssm.StringParameter(
    stack_under_test,
    "forward-function-name",
    string_value=stack_under_test.notification_function.function_name,
    parameter_name=("/hls/tests/forward-function-name"),
)

for k, v in dict(
    Project="hls",
    App="forward-it",
).items():
    Tags.of(app).add(k, v, apply_to_launched_instances=True)

app.synth()
