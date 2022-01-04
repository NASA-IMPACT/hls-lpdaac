import os
from typing import List

from setuptools import find_packages, setup  # type: ignore

with open(os.path.join(os.environ.get("PWD", "."), ".cdk-version"), "r") as f:
    aws_cdk_version = f.read()

aws_cdk_extras = [
    f"aws_cdk.{aws_cdk_package}=={aws_cdk_version}"
    for aws_cdk_package in [
        "core",
        "assertions",
        "aws-events",
        "aws-events-targets",
        "aws-iam",
        "aws-lambda",
        "aws-lambda-python",
        "aws-s3",
        "aws-sqs",
    ]
]

install_requires: List[str] = []

extras_require = {
    "test": [
        *aws_cdk_extras,
        "flake8",
        "black",
        "pytest-cov",
        "pytest",
    ],
    "dev": [
        *aws_cdk_extras,
        "black",
        "boto3",
        "boto3-stubs[essential]",
        "botocore-stubs",
        "flake8",
        "isort",
        "mypy",
        "nodeenv",
        "pre-commit",
        "pre-commit-hooks",
        "pytest",
    ],
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
