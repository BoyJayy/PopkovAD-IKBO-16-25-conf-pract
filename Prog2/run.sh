#!/bin/sh
set -eu
base=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
exec "${PYTHON:-python3}" "$base/src/main.py" "$@"
