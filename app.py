#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

from hls_lpdaac.hls_lpdaac_stack import HlsLpdaacStack

STACK = os.environ["HLS_LPDAAC_STACK"]

app = cdk.App()

# For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
HlsLpdaacStack(
    app,
    STACK,
    permissions_boundary_arn=os.getenv("HLS_LPDAAC_PERMISSIONS_BOUNDARY_ARN"),
)

for k, v in dict(
    Project="hls",
    Stack=STACK,
).items():
    cdk.Tags.of(app).add(k, v, apply_to_launched_instances=True)

app.synth()
