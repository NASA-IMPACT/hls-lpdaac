APPS=$(subst _,-,$(patsubst cdk/app_%.py,%,$(wildcard cdk/app_*.py)))
IT_APPS=$(subst _,-,$(patsubst cdk/app_%.py,%,$(wildcard cdk/app_*_it.py)))
RECREATE=
SHELL=/usr/bin/env bash
TOX=tox $(TOX_OPTS)
TOX_OPTS?=
VENV_TOX_LOG_LOCK=.venv/.tox-info.json

.PHONY: help bootstrap install-cdk install-node tox unit-tests venv
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

# Set the tox --recreate option when setup.py is newer than the tox log lock
# file in the virtualenv, as that indicates it was updated since the last time
# tox was run.  This allows us to develop more quickly by avoiding unnecessary
# environment recreation, while ensuring that the environment is recreated when
# necessary (i.e., when dependencies change).
$(VENV_TOX_LOG_LOCK): setup.py
	$(eval RECREATE := --recreate)

# Rules that run a tox command should depend on this to make sure the virtualenv
# is updated when necessary, without unnecessarily specifying the tox --recreate
# option explicitly.
venv: $(VENV_TOX_LOG_LOCK)

tox:
	@if [[ -z $${TOX_ENV_DIR} ]]; then \
	    echo "ERROR: For tox.ini use only" >&2; \
	    exit 1; \
	fi

# NOTE: Intended only for use from tox.ini.
# Install Node.js within the tox virtualenv.
install-node: tox
	type node || nodeenv --node lts --python-virtualenv

# NOTE: Intended only for use from tox.ini
# Install the CDK CLI within the tox virtualenv.
install-cdk: install-node
	npm install --location global "aws-cdk@latest"

## bootstrap: Bootstrap the CDK toolkit
bootstrap:
	$(TOX) $(RECREATE) -e dev -- bootstrap \
	    --toolkit-stack-name CDKToolkitV2 \
	    --custom-permissions-boundary mcp-tenantOperator \
	    --template cdk/bootstrap-template.yaml

## unit-tests: Run unit tests
unit-tests: venv
	$(TOX) $(RECREATE)

## APP-integration-tests: Run integration tests for a CDK app (depends on deploy-APP-it)
$(patsubst %-it,%-integration-tests,$(IT_APPS)): venv
	$(TOX) $(RECREATE) -e integration -- $(wildcard tests/integration/test_$(subst -integration-tests,,$@)*.py)

## synth-APP: Synthesize a CDK app
$(patsubst %,synth-%,$(APPS)): venv
	$(TOX) $(RECREATE) -e dev -- synth --all --app $(subst -,_,$(patsubst synth-%,cdk/app_%.py,$@))

## diff-APP: Diff a CDK app
$(patsubst %,diff-%,$(APPS)): venv
	$(TOX) $(RECREATE) -e dev -- diff --all --app $(subst -,_,$(patsubst diff-%,cdk/app_%.py,$@))

## deploy-APP: Deploy a CDK app
$(patsubst %,deploy-%,$(APPS)): venv
	$(TOX) $(RECREATE) -e dev -- deploy --all --app $(subst -,_,$(patsubst deploy-%,cdk/app_%.py,$@)) --progress events --require-approval never

## destroy-APP: Destroy a CDK app
$(patsubst %,destroy-%,$(APPS)): venv
	$(TOX) $(RECREATE) -e dev -- destroy --all --app $(subst -,_,$(patsubst destroy-%,cdk/app_%.py,$@)) --progress events --force
