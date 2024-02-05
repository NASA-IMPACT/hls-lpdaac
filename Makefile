APPS=$(subst _,-,$(patsubst cdk/app_%.py,%,$(wildcard cdk/app_*.py)))
IT_APPS=$(subst _,-,$(patsubst cdk/app_%.py,%,$(wildcard cdk/app_*_it.py)))
# CDK version must match the version specified in setup.py
CDK_VERSION=1.204.0
NODE_VERSION=18.18.2
RECREATE=
SHELL=/usr/bin/env bash
TOX=tox $(TOX_OPTS)
TOX_OPTS?=
VENV_TOX_LOG_LOCK=.venv/.tox-info.json

.PHONY: help
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
	if [[ -z $${TOX_ENV_DIR+x} ]]; then \
	    echo "ERROR: For tox.ini use only" >&2; \
	    exit 1; \
	fi

# NOTE: Intended only for use from tox.ini.
# Install Node.js within the tox virtualenv.
install-node: tox
	# Install node in the virtualenv, if it's not installed or it's the wrong version.
	if [[ ! $$(type node 2>/dev/null) =~ $${VIRTUAL_ENV} || ! $$(node -v) =~ $(NODE_VERSION) ]]; then \
	    nodeenv --node $(NODE_VERSION) --python-virtualenv; \
	fi

# NOTE: Intended only for use from tox.ini
# Install the CDK CLI within the tox virtualenv.
install-cdk: tox install-node
	# Install cdk in the virtualenv, if it's not installed or it's the wrong version.
	if [[ ! $$(type cdk 2>/dev/null) =~ $${VIRTUAL_ENV} || ! $$(cdk --version) =~ $(CDK_VERSION) ]]; then \
	    npm install --location global "aws-cdk@$(CDK_VERSION)"; \
	fi
  	# Acknowledge CDK notice regarding CDK v1 being in maintenance mode.
	grep -q 19836 cdk.context.json 2>/dev/null || cdk acknowledge 19836

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
