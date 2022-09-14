from aws_cdk import aws_s3 as s3
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_ssm as ssm
from aws_cdk import core as cdk


class HlsLpdaacIntegrationStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, id: str) -> None:
        super().__init__(scope, id)

        self.bucket = s3.Bucket(self, "test-bucket")
        self.queue = sqs.Queue(self, "test-queue")

        # Set SSM Parameters for use within integration tests

        ssm.StringParameter(
            self,
            "bucket_name",
            string_value=self.bucket.bucket_name,
            parameter_name=("/tests/bucket_name"),
        )

        ssm.StringParameter(
            self,
            "queue_name",
            string_value=self.queue.queue_name,
            parameter_name=("/tests/queue_name"),
        )
