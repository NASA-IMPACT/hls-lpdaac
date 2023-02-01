#!/usr/bin/env python3

from aws_cdk import aws_iam as iam
from aws_cdk import aws_ssm as ssm
from aws_cdk import core as cdk

from stacks import HlsLpdaacIntegrationStack, HlsLpdaacStack

ci_app = cdk.App()
account_id = iam.AccountRootPrincipal().account_id

int_stack = HlsLpdaacIntegrationStack(
    ci_app,
    "integration-test-resources",
    managed_policy_name="mcp-tenantOperator",
)
stack_under_test = HlsLpdaacStack(
    ci_app,
    "hls-lpdaac-under-test",
    bucket_name=int_stack.bucket.bucket_name,
    queue_arn=int_stack.queue.queue_arn,
    managed_policy_name="mcp-tenantOperator",
)

# Set SSM Parameter for use within integration tests

ssm.StringParameter(
    stack_under_test,
    "function_name",
    string_value=stack_under_test.lpdaac_historical_lambda.function_name,
    parameter_name=("/tests/function_name"),
)

for k, v in dict(
    Project="hls",
    Stack="lpdaac-integration",
).items():
    cdk.Tags.of(ci_app).add(k, v, apply_to_launched_instances=True)

ci_app.synth()
