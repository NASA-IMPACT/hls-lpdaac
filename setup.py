import os
from typing import List

from setuptools import find_packages, setup  # type: ignore

aws_cdk_extras = [
    f"aws_cdk.{aws_cdk_package}<2"
    for aws_cdk_package in [
        "core",
        "assertions",
        "aws-events",
        "aws-events-targets",
        "aws-iam",
        "aws-lambda",
        "aws-lambda-python",
        "aws-s3",
        "aws-s3-notifications",
        "aws-sqs",
    ]
]

install_requires: List[str] = []

extras_require_test = [
    *aws_cdk_extras,
    "flake8",
    "black",
    "boto3",
    "moto[s3,sqs]",
    "pytest-cov",
    "pytest",
]

extras_require_dev = [
    *extras_require_test,
    "aws_lambda_typing",
    "boto3-stubs[iam,lambda,s3,sqs]",
    "botocore-stubs",
    "isort",
    "mypy",
    "nodeenv",
    "pre-commit",
    "pre-commit-hooks",
    "pyright",
]

extras_require = {
    "test": extras_require_test,
    "dev": extras_require_dev,
}

setup(
    name="hls-lpdaac",
    version="0.0.1",
    python_requires=">=3.9",
    author="Development Seed",
    packages=find_packages(),
    package_data={
        ".": [
            "cdk.json",
        ],
    },
    install_requires=install_requires,
    extras_require=extras_require,
    include_package_data=True,
)
