# HLS LPDAAC

## Requirements

- [pre-commit](https://pre-commit.com/)
- Python >= 3.9
- tox
- AWS CLI
- AWS IAM role with sufficient permissions for creating, destroying and modifying relevant stack resources

## Environment Settings

```plain
export AWS_PROFILE=<profile name>
export AWS_REGION=<region>
export HLS_LPDAAC_STACK=<stack name>
export HLS_LPDAAC_PERMISSIONS_BOUNDARY_ARN=<arn>
```

## CDK Commands

### Synth

Display generated cloud formation template that will be used to deploy.

```plain
tox -e dev -r -- synth
```

### Diff

Display a diff of the current deployment and any changes created.

```plain
tox -e dev -r -- diff || true
```

### Deploy

Deploy current version of stack.

```plain
tox -e dev -r -- deploy
```

## Development

For active stack development run

```plain
tox -e dev -r -- version
```

This creates a local virtualenv in the directory `.venv-dev`.
To use it for development:

```plain
source .venv-dev/bin/activate
```

## Tests

To run unit tests:

```plain
tox -r
```
