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
export HLS_LPDAAC_MANAGED_POLICY_NAME=mcp-tenantOperator

# Optional notification delivery controls (defaults shown)
export HLS_LPDAAC_PAUSED=false
export HLS_LPDAAC_MAX_CONCURRENCY=5
export HLS_LPDAAC_BATCH_SIZE=10
```

## Pausing notifications during an LPDAAC maintenance window

S3 object-created notifications are delivered to a queue owned by this stack,
which the forwarder Lambda consumes through an SQS event source mapping. While
the mapping is disabled, notifications accumulate in that queue (14 day
retention) and are forwarded once it is re-enabled.

The `HLS_LPDAAC_PAUSED` GitHub environment variable is the single source of
truth for whether a stack is paused. Every deploy, manual or automatic, reads
it, so a merge to `develop` or a published release during a maintenance window
keeps the stack paused.

To pause, set the variable on the affected environment and redeploy:

```plain
gh variable set HLS_LPDAAC_PAUSED --env prod-forward --body true
gh workflow run deploy.yml -f environment=prod-forward -f target=forward
```

To resume, set it back to `false` (or delete it) and redeploy:

```plain
gh variable set HLS_LPDAAC_PAUSED --env prod-forward --body false
gh workflow run deploy.yml -f environment=prod-forward -f target=forward
```

Do not disable the event source mapping with the AWS CLI or console: the next
deploy reconciles it back to the value declared by CDK.

`HLS_LPDAAC_MAX_CONCURRENCY` caps concurrent forwarder invocations, smoothing
bursts of notifications sent to LPDAAC, and is changed the same way.

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
