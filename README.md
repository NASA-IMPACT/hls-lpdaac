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
export AWS_PROFILE=<profile name>
export AWS_REGION=<region>
export HLS_LPDAAC_STACK=<stack name>
export HLS_LPDAAC_BUCKET_NAME=<source bucket name>
export HLS_LPDAAC_QUEUE_ARN=<destination queue ARN>

# Optional
export HLS_LPDAAC_MANAGED_POLICY_NAME=<(e.g., mcp-tenantOperator)>
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
tox -e dev -r -- version
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
