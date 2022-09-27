# HLS LPDAAC

## Requirements

- [pre-commit](https://pre-commit.com/)
- Python >= 3.9
- tox
- AWS CLI
- AWS IAM role with sufficient permissions for creating, destroying and modifying
  relevant stack resources

## Environment Settings

```plain
# AWS_PROFILE (or id, key, and token) required only when running locally
export AWS_PROFILE=<profile name>

export AWS_DEFAULT_REGION=us-west-2
export HLS_LPDAAC_BUCKET_NAME=<source bucket name>
export HLS_LPDAAC_MANAGED_POLICY_NAME=<(e.g., mcp-tenantOperator)>
export HLS_LPDAAC_QUEUE_ARN=<destination queue ARN>
export HLS_LPDAAC_STACK=<stack name>
```

## CDK Commands

### Synth

Display generated cloud formation template that will be used to deploy.

```plain
make synth
```

### Diff

Display a diff of the current deployment and any changes created.

```plain
make diff
```

### Deploy

Deploy current version of stack:

```plain
make deploy
```

### Destroy

Destroy current version of stack:

```plain
make destroy
```

### Development

For active stack development run

```plain
tox -e dev -- version
```

This creates a local virtualenv in the directory `.venv-dev`.
To use it for development:

```plain
source .venv-dev/bin/activate
```

Install pre-commit hooks:

```plain
pre-commit install --install-hooks
```

The command above will make sure all pre-commit hooks configured in
`.pre-commit-config.yaml` are executed when appropriate.

To manually run the hooks to check code changes:

```plain
pre-commit run --all-files
```

### Tests

To run unit tests:

```plain
make unit-tests
```

To run integration tests:

```plain
make ci-deploy
make integration-tests
make ci-destroy
```

## Deployment Using an EC2 Instance

Create an EC2 instance:

- **AMI:** `ami-07d249fe97e5e7a77` (MCP Ubuntu 20.04 20220801T230742), which can be
  found under "My AMIs > Shared with me"
- **Instance type:** `t3-small`
- **Security group:** `launch-wizard-1` (`sg-0e915c4a88d790e96`), which allows SSH
- **Advanced details > IAM instance profile:** `hls-stack-deploy`

Once the instance if ready, connect to it via either Session Manager or SSH, and run
the following commands to install the required packages:

```plain
sudo apt update
sudo apt install -y --no-install-recommends make python3.9-dev tox
```

Next, you must clone this repository, but to do so, you need to create a GitHub personal
access token, which you then need to use as your password, when prompted for it during
the clone operation.  Once you have a GitHub personal access token, continue with the
following commands within your Session Manager or SSH session:

```plain
bash
cd ~
git clone https://github.com/NASA-IMPACT/hls-lpdaac.git
cd hls-lpdaac
```

At this point, follow the instructions above for Environment Settings and you
should then be able to run unit tests and integration tests as described above.
