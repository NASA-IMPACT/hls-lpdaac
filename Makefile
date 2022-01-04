SHELL=/usr/bin/env bash

.PHONY: tox

tox:
	if [ -z $${TOX_ENV_DIR+x} ]; then echo "USE TOX"; exit 1; fi

# NOTE: Intended only for use from tox.ini.
#
# Install Node.js within the tox venv, if it is not already installed there
# or if what is already installed there is not the correct version, as specified
# in the .nvmrc file.
install-node: tox
	node_path=$$(builtin type -P node) && \
	actual_version=$$(node --version 2>/dev/null) && \
	expected_version=$$(<"$${PWD}/.nvmrc") && \
	if ! [[ "$${node_path}" =~ ^$${TOX_ENV_DIR} && "$${actual_version}" =~ $${expected_version} ]]; then \
	  nodeenv --node="$${expected_version}" -p; \
	fi

# NOTE: Intended only for use from tox.ini.
#
# Install the CDK CLI within the tox venv, if it is not already installed there
# or if what is already installed there is not the correct version, as specified
# in the .cdk-version file.
install-cdk: install-node
	cdk_path=$$(builtin type -P cdk) && \
	actual_version=$$(cdk --version 2>/dev/null) && \
	expected_version=$$(<"$${PWD}/.cdk-version") && \
	if ! [[ "$${cdk_path}" =~ ^$${TOX_ENV_DIR} && "$${actual_version}" =~ $${expected_version} ]]; then \
	  npm install -g "aws-cdk@$${expected_version}"; \
	fi
