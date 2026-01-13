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
# AWS Short-term Access Key

export AWS_DEFAULT_REGION=us-west-2
export AWS_ACCESS_KEY_ID=<id>
export AWS_SECRET_ACCESS_KEY=<key>
export AWS_SESSION_TOKEN=<token>

# Stack variables

export HLS_LPDAAC_STACK=<stack name>
export HLS_LPDAAC_BUCKET_NAME=<source bucket name>
export HLS_LPDAAC_QUEUE_ARN=<destination queue ARN>
# Required ONLY in PROD for FORWARD processing (otherwise, a dummy queue is created)
export HLS_LPDAAC_TILER_QUEUE_ARN=<tiler queue ARN>
export HLS_LPDAAC_MANAGED_POLICY_NAME=mcp-tenantOperator
```

## CDK Commands

In the `make` commands shown below, `<APP>` must be one of the following:

- `forward`
- `forward-it` (integration test stack)
- `historical`
- `historical-it` (integration test stack)

### Synth

Display generated cloud formation template that will be used to deploy.

```plain
make synth-<APP>
```

### Diff

Display a diff of the current deployment and any changes created.

```plain
make diff-<APP>
```

### Deploy

Deploy current version of stack:

```plain
make deploy-<APP>
```

### Destroy

Destroy current version of stack:

```plain
make destroy-<APP>
```

### Development

For active stack development run

```plain
tox -e dev -r -- version
```

This creates a local virtualenv in the directory `.venv`.
To use it for development:

```plain
source .venv/bin/activate
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

To run integration tests for forward processing:

```plain
make deploy-forward-it
make forward-integration-tests
make destroy-forward-it
```

To run integration tests for historical processing:

```plain
make deploy-historical-it
make historical-integration-tests
make destroy-historical-it
```
