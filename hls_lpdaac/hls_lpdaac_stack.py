from typing import Optional

from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_notifications as s3n
from aws_cdk import aws_sqs as sqs
from aws_cdk import core as cdk


def queue_arn_from_url(queue_url: str) -> str:
    # https://sqs.us-west-2.amazonaws.com/611670965994/test1
    # arn:aws:sqs:us-west-2:611670965994:test1
    [*_, host, account, name] = queue_url.split("/")
    [_, region, *_] = host.split(".")

    return f"arn:aws:sqs:{region}:{account}:{name}"


class HlsLpdaacStack(cdk.Stack):
    def __init__(
        self,
        scope: cdk.Construct,
        stack_name: str,
        *,
        bucket_name: str,
        queue_url: str,
        permissions_boundary_arn: Optional[str] = None,
    ) -> None:
        super().__init__(scope, stack_name)

        if permissions_boundary_arn:
            iam.PermissionsBoundary.of(self).apply(
                iam.ManagedPolicy.from_managed_policy_arn(
                    self, "PermissionsBoundary", permissions_boundary_arn
                )
            )

        self.lpdaac_historical_role = iam.Role(
            self,
            "LpdaacHistoricalRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )

        self.lpdaac_historical_lambda = lambda_.Function(
            self,
            "LpdaacHistoricalLambda",
            code=lambda_.Code.from_asset("hls_lpdaac/lpdaac/historical"),
            handler="index.handler",
            runtime=lambda_.Runtime.PYTHON_3_9,  # type: ignore
            memory_size=128,
            timeout=cdk.Duration.seconds(30),
            role=self.lpdaac_historical_role,  # type: ignore
            environment=dict(QUEUE_URL=queue_url),
        )

        self.lpdaac_historical_bucket = s3.Bucket.from_bucket_name(
            self, "LpdaacHistoricalBucket", bucket_name
        )
        self.lpdaac_historical_bucket.grant_read(self.lpdaac_historical_role)

        queue_arn = queue_arn_from_url(queue_url)
        self.lpdaac_historical_queue = sqs.Queue.from_queue_arn(
            self, "LpdaacHistoricalQueue", queue_arn=queue_arn
        )
        self.lpdaac_historical_queue.grant_send_messages(self.lpdaac_historical_role)

        self.lpdaac_historical_bucket.add_object_created_notification(
            s3n.LambdaDestination(self.lpdaac_historical_lambda),  # type: ignore
            s3.NotificationKeyFilter(suffix=".v2.0.json"),
        )
