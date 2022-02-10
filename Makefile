SHELL=/usr/bin/env bash

.PHONY: tox

tox:
	if [ -z $${TOX_ENV_DIR+x} ]; then echo "USE TOX"; exit 1; fi

# NOTE: Intended only for use from tox.ini.
#
# Install Node.js within the tox virtualenv, if it is not already installed.
install-node:
	node_path=$$(builtin type -P node) && \
	if ! [[ "$${node_path}" =~ ^$${TOX_ENV_DIR} ]]; then \
	  nodeenv --node lts --python-virtualenv; \
	fi

# NOTE: Intended only for use from tox.ini
#
# Install the CDK CLI within the tox virtualenv, if it is not already installed.
install-cdk: tox install-node
	cdk_path=$$(builtin type -P cdk) && \
	if ! [[ "$${cdk_path}" =~ ^$${TOX_ENV_DIR} ]]; then \
	  npm install -g "aws-cdk@1.x"; \
	fi
