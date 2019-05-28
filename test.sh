#!/usr/bin/env bash
set -eo pipefail
pip install tox
export TOXENV=$(tox --listenvs | grep "^${1}")
tox
