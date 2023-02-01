# CDK version must match the version specified in setup.py
CDK_VERSION=1.176.0
NODE_VERSION=16.17.1
RECREATE=
SHELL=/usr/bin/env bash
TOX=tox $(TOX_OPTS)
TOX_OPTS?=-v
VENV_TOX_LOG_LOCK=.venv/log/.lock

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

## integration-tests: Run integration tests (requires ci-deploy)
integration-tests: venv
	$(TOX) $(RECREATE) -e integration $(RECREATE)

## synth: Run CDK synth
synth: venv
	$(TOX) $(RECREATE) -e dev -- synth '*' --app cdk/app.py

## deploy: Run CDK deploy
deploy: venv
	$(TOX) $(RECREATE) -e dev -- deploy '*' --app cdk/app.py --progress events --require-approval never

## diff: Run CDK diff
diff: venv
	$(TOX) $(RECREATE) -e dev -- diff '*' --app cdk/app.py

## destroy: Run CDK destroy
destroy: venv
	$(TOX) $(RECREATE) -e dev -- destroy --force '*' --app cdk/app.py --progress events

## ci-synth: Run CDK synth for integration stack
ci-synth: venv
	$(TOX) $(RECREATE) -e dev -- synth '*' --app cdk/app_ci.py

## ci-deploy: Run CDK deploy for integration stack
ci-deploy: venv
	$(TOX) $(RECREATE) -e dev -- deploy '*' --app cdk/app_ci.py --progress events --require-approval never

## ci-diff: Run CDK diff for integration stack
ci-diff: venv
	$(TOX) $(RECREATE) -e dev -- diff '*' --app cdk/app_ci.py

## ci-destroy: Run CDK destroy for integration stack
ci-destroy: venv
	$(TOX) $(RECREATE) -e dev -- destroy --force '*' --app cdk/app_ci.py --progress events
