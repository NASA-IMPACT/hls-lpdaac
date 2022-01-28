#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

from hls_lpdaac.hls_lpdaac_stack import HlsLpdaacStack

# Required environment variables
stack_name = os.environ["HLS_LPDAAC_STACK"]
bucket_name = os.environ["HLS_LPDAAC_BUCKET_NAME"]
queue_url = os.environ["HLS_LPDAAC_QUEUE_URL"]

# Optional environment variables
permissions_boundary_arn = os.getenv("HLS_LPDAAC_PERMISSIONS_BOUNDARY_ARN")

app = cdk.App()

# For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
HlsLpdaacStack(
    app,
    stack_name,
    bucket_name=bucket_name,
    queue_url=queue_url,
    permissions_boundary_arn=permissions_boundary_arn,
)

for k, v in dict(
    Project="hls",
    Stack=stack_name,
).items():
    cdk.Tags.of(app).add(k, v, apply_to_launched_instances=True)

app.synth()
