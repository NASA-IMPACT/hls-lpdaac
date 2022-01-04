import os
from typing import Dict, List, Literal, TypedDict

import boto3


class S3Object(TypedDict):
    bucket: Dict[Literal["name"], str]
    object: Dict[Literal["key"], str]


class S3Event(TypedDict):
    Records: List[Dict[Literal["s3"], S3Object]]


def handler(event: S3Event, _):
    s3 = boto3.resource("s3")
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    message = s3.Object(bucket, key).get()["Body"].read().decode("utf-8")

    #
    # Why don't we use a bucket tag to specify the queue URL?
    #
    # Doing so would have the following benefits: (a) eliminate the if/else,
    # (b) eliminate the env var, (c) eliminate hard-coded bucket names.
    #
    # For example:
    #
    #   queue_url = bucket.Tagging().tag_set["queue-url"]
    #

    if bucket == "hls-dev-global-v2-historical":
        queue_url = os.environ["UAT_QUEUE_URL"]
    elif bucket == "hls-global-v2-historical":
        queue_url = os.environ["PROD_QUEUE_URL"]

    sqs = boto3.client("sqs", region_name=queue_url.split(".")[1])
    response = sqs.send_message(QueueUrl=queue_url, MessageBody=message)
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]

    print(f"Status Code - {status_code} - {key}")
