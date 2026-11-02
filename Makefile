APPS=$(subst _,-,$(patsubst cdk/app_%.py,%,$(wildcard cdk/app_*.py)))
IT_APPS=$(subst _,-,$(patsubst cdk/app_%.py,%,$(wildcard cdk/app_*_it.py)))
SHELL=/usr/bin/env bash
UV?=uv
UV_RUN=$(UV) run
NODE_STAMP=.venv/.node-installed
CDK_STAMP=.venv/.cdk-installed

.PHONY: help cdk-cli check format install lint sync typecheck unit-tests
.DEFAULT_GOAL := help

help: Makefile
	@echo
	@echo "Usage: make [options] target ..."
	@echo
	@echo "Options:"
	@echo "  Run 'make -h' to list options."
	@echo
	@echo "Targets:"
	@sed -n 's/^##//p' $< | column -t -s ':' | sed -e 's/^/ /'
	@echo
	@printf "  where APP is one of the following:\n$(patsubst %,\n  - %,$(APPS))\n"
	@echo

## sync: Create/update the virtualenv in .venv from uv.lock
sync:
	$(UV) sync

## install: Set up the virtualenv and the pre-commit hooks
install: sync
	$(UV_RUN) pre-commit install --install-hooks

# The CDK CLI is a Node package, so install Node into .venv and the CLI beside
# it. Both are stamped so this runs once per virtualenv rather than per command.
$(NODE_STAMP):
	$(UV_RUN) nodeenv --node lts --python-virtualenv
	@touch $@

$(CDK_STAMP): $(NODE_STAMP)
	$(UV_RUN) npm install --location global "aws-cdk@latest"
	@touch $@

## cdk-cli: Install the CDK CLI into .venv (implied by the CDK targets below)
cdk-cli: $(CDK_STAMP)

## lint: Check formatting and lint with ruff
lint:
	$(UV_RUN) ruff format --check .
	$(UV_RUN) ruff check .

## format: Apply ruff formatting and lint autofixes
format:
	$(UV_RUN) ruff check --fix .
	$(UV_RUN) ruff format .

## typecheck: Type check with mypy
typecheck:
	$(UV_RUN) mypy

## unit-tests: Run unit tests
unit-tests:
	$(UV_RUN) pytest -vv --cov src --cov-report term-missing tests/unit

## check: Run lint, typecheck and unit tests
check: lint typecheck unit-tests

## bootstrap: Bootstrap the CDK toolkit
bootstrap: cdk-cli
	$(UV_RUN) cdk bootstrap \
	    --toolkit-stack-name CDKToolkitV2 \
	    --custom-permissions-boundary mcp-tenantOperator-APIG \
	    --template cdk/bootstrap-template.yaml

## APP-integration-tests: Run integration tests for a CDK app (depends on deploy-APP-it)
$(patsubst %-it,%-integration-tests,$(IT_APPS)):
	$(UV_RUN) pytest -vv $(wildcard tests/integration/test_$(subst -integration-tests,,$@)*.py)

## synth-APP: Synthesize a CDK app
$(patsubst %,synth-%,$(APPS)): cdk-cli
	$(UV_RUN) cdk synth --all --app $(subst -,_,$(patsubst synth-%,cdk/app_%.py,$@))

## diff-APP: Diff a CDK app
$(patsubst %,diff-%,$(APPS)): cdk-cli
	$(UV_RUN) cdk diff --all --app $(subst -,_,$(patsubst diff-%,cdk/app_%.py,$@))

## deploy-APP: Deploy a CDK app
$(patsubst %,deploy-%,$(APPS)): cdk-cli
	$(UV_RUN) cdk deploy --all --app $(subst -,_,$(patsubst deploy-%,cdk/app_%.py,$@)) --progress events --require-approval never

## destroy-APP: Destroy a CDK app
$(patsubst %,destroy-%,$(APPS)): cdk-cli
	$(UV_RUN) cdk destroy --all --app $(subst -,_,$(patsubst destroy-%,cdk/app_%.py,$@)) --progress events --force
