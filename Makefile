SHELL=/usr/bin/env bash

.PHONY: help tox
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

tox:
	if [ -z $${TOX_ENV_DIR+x} ]; then echo "ERROR: For tox.ini use only" >&2; exit 1; fi

# NOTE: Intended only for use from tox.ini.
# Install Node.js within the tox virtualenv.
install-node: tox
	nodeenv --node 16.17.0 --python-virtualenv

# NOTE: Intended only for use from tox.ini
# Install the CDK CLI within the tox virtualenv.
install-cdk: tox install-node
	npm install --location global "aws-cdk@1.x"
  	# Acknowledge CDK notice regarding CDK v1 being in maintenance mode.
	grep -q 19836 cdk.context.json 2>/dev/null || cdk acknowledge 19836

## unit-tests: Run unit tests
unit-tests:
	tox -v -r

## integration-tests: Run integration tests (requires ci-deploy)
integration-tests:
	tox -v -e integration -r

## synth: Run CDK synth
synth:
	tox -v -e dev -r -- synth '*' --app cdk/app.py

## deploy: Run CDK deploy
deploy:
	tox -v -e dev -r -- deploy '*' --app cdk/app.py --progress events --require-approval never

## diff: Run CDK diff
diff:
	tox -v -e dev -r -- diff '*' --app cdk/app.py

## destroy: Run CDK destroy
destroy:
	tox -v -e dev -r -- destroy --force '*' --app cdk/app.py --progress events

## ci-synth: Run CDK synth for integration stack
ci-synth:
	tox -v -e dev -r -- deploy '*' --app cdk/app_ci.py

## ci-deploy: Run CDK deploy for integration stack
ci-deploy:
	tox -v -e dev -r -- deploy '*' --app cdk/app_ci.py --progress events --require-approval never

## ci-diff: Run CDK diff for integration stack
ci-diff:
	tox -v -e dev -r -- diff '*' --app cdk/app_ci.py

## ci-destroy: Run CDK destroy for integration stack
ci-destroy:
	tox -v -e dev -r -- destroy --force '*' --app cdk/app_ci.py --progress events
