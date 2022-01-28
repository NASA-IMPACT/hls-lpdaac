import os

import boto3
from aws_lambda_typing.context import Context
from aws_lambda_typing.events import S3Event

s3 = boto3.resource("s3")


def handler(event: S3Event, _: Context) -> None:
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    message = s3.Object(bucket, key).get()["Body"].read().decode("utf-8")

    queue_url = os.environ["QUEUE_URL"]
    sqs = boto3.client("sqs", region_name=queue_url.split(".")[1])
    response = sqs.send_message(QueueUrl=queue_url, MessageBody=message)
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]

    print(f"Status Code - {status_code} - {key}")
